//Esercizio Laboratorio 2 (Unione parti del Lab1) Local Smart Home
#include <LiquidCrystal_PCF8574.h>
#include <Scheduler.h>
#include <MBED_RPi_Pico_TimerInterrupt.h>
#include <PDM.h>

int RLED= 2; //Per ricordarsi i pin utilizzati
int YLED= 3;
int PIRPIN= 7;
int FANPIN= 5; 
int TEMPPIN = A0; //14
const int B=4275;
const long int R0=100000;
const int T0= 298.13;
volatile float T=0.0;
int potSpeed=0;
int brightness=0;
LiquidCrystal_PCF8574 lcd(0x27); 
volatile int minHeat; //Temperature per riscaldamento led
volatile int maxHeat;
volatile int minCond; //temperature aria condizionata ventola
volatile int maxCond;
const int valHeat[]={15, 20, 10, 15};
const int valCond[]={25, 30, 20, 25};
volatile int numPeoplePir=0;
volatile int numPeopleMic=0;
const int timeout_pir= 1000*60*2; //2 minuti
volatile long int lastTimeReadPir=0;
const int n_sound_events=10;
const int sound_interval= 1000*60*1;//1 minuti
const int sound_threshold=1500;
const int timeout_sound=1000*60*1; //1 minuti
volatile int timeSoundEvents[10];
volatile int lastTimeReadMic=0;
volatile int firstTimeReadMic=0;
short sampleBuffer[512];
volatile int numSounds=0;

void setup() {
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Exercise Lab 2: Local Smart Home");
  lcd.begin(16, 2);
  lcd.setBacklight(255);
  lcd.home();
  lcd.clear();
  pinMode(RLED, OUTPUT);
  pinMode(TEMPPIN, INPUT);
  pinMode(FANPIN, OUTPUT);
  digitalWrite(FANPIN, potSpeed);
  setPointsWithOutPeople();
  Scheduler.startLoop(printOnLcd);
  attachInterrupt(digitalPinToInterrupt(PIRPIN), checkPresence, CHANGE);

  PDM.onReceive(onPDMdata);
  if (!PDM.begin(1, 20000)) {
    Serial.println("Failed to start PDM!");
    while (1);
  }
}

void loop() {
  int V= analogRead(TEMPPIN);
  float R= (1023.0/(float)V -1.0)*R0; 
  T= 1.0/(log(R/R0)/B + (1.0/T0)) - 273.1;
  if(T >= minCond)
  {
    potSpeed= map(T, minCond, maxCond, 0, 255);
    analogWrite(FANPIN, potSpeed);
  }
  else if(T >= minHeat && T <=maxHeat)
  {
    brightness= map(T, minHeat, maxHeat, 255, 0);
    analogWrite(RLED, brightness);
  }

  long int now=millis();
  if((now-lastTimeReadPir)> timeout_pir)
  {
    numPeoplePir=0;
  }

  if((now-lastTimeReadMic) >timeout_sound)
  {
    numPeopleMic=0;
    numSounds=0;
    firstTimeReadMic=0;
    lastTimeReadMic=0;
  }

  if((numPeopleMic+ numPeoplePir) == 0)
  {
    setPointsWithOutPeople();
  }

}

void setPointsWithPeople()
{
  minCond=valCond[2];
  maxCond=valCond[3];
  minHeat=valHeat[2];
  maxHeat=valHeat[3];
}

void setPointsWithOutPeople()
{
  minCond=valCond[0];
  maxCond=valCond[1];
  minHeat=valHeat[0];
  maxHeat=valHeat[1];
}
void checkPresence()
{
  lastTimeReadPir=millis();
  numPeoplePir+=1;
  setPointsWithPeople();
}

void onPDMdata()
{
  int bytesAvailable= PDM.available();
  PDM.read(sampleBuffer, bytesAvailable);
  int samplesRead=bytesAvailable/2;

  for(int i=0; i<samplesRead; i++)
  {
    if(sampleBuffer[i] > sound_threshold)
    {
      lastTimeReadMic=millis();
      numSounds++;
      break;
    }
  }

  if(numPeopleMic++;(firstTimeReadMic- lastTimeReadMic) > sound_interval && numSounds > n_sound_events)
  {
    setPointsWithPeople();
  }
}

void printOnLcd()
{
  int numPeople=numPeoplePir+ numPeopleMic;
  lcd.print("T: ");
  lcd.print(T);
  lcd.print("P:");
  lcd.print(numPeopleMic); //Prova per verifica
  lcd.print(" ");
  lcd.print(numPeoplePir); //Prova per verifica
  lcd.setCursor(0,1);
  lcd.print("AC: ");
  lcd.print(potSpeed);
  lcd.print(" HT: ");
  lcd.print(brightness);
  lcd.print(" ");
  delay(5*1000);
  lcd.setCursor(1,0);
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("AC m:");
  lcd.print(minCond);
  lcd.print(" M:");
  lcd.print(maxCond);
  lcd.setCursor(0,1);
  lcd.print("HT m:");
  lcd.print(minHeat);
  lcd.print(" M:");
  lcd.print(maxHeat);
  delay(5*1000);
  lcd.setCursor(1,0);
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.clear();
  lcd.setCursor(0,0);
}