//Esercizio Laboratorio 2 (Unione parti del Lab1) Local Smart Home
#include <LiquidCrystal_PCF8574.h>
#include <Scheduler.h>
#include <MBED_RPi_Pico_TimerInterrupt.h>
#include <PDM.h>

int RLED= 2; //Pin utilizzati
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
volatile int timeSoundEvents[n_sound_events]; //Buffer circolare per i tempi legati agli eventi ascoltati dal microfono
volatile int firstPos=0; //Indici per il buffer circolare
volatile int lastPos=-1; //inizia da -1 così che alla prima lettura viene messo a 0
short sampleBuffer[512];
volatile int numSounds=0;

void setup() {
  //Setup della porta seriale
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Exercise Lab 2: Local Smart Home");
  Serial.println("Per settare i valori di soglia scriverli nell'ordine:  minAC maxAC minHeat maxHeat (di fila e separati da uno spazio)");
  //Setup dello schermo LCD
  lcd.begin(16, 2);
  lcd.setBacklight(255);
  lcd.home();
  lcd.clear();

  //Setup dei pin del led, del sensore di temperatura, della ventola e del sensore pir
  pinMode(RLED, OUTPUT);
  pinMode(TEMPPIN, INPUT);
  pinMode(FANPIN, OUTPUT);
  digitalWrite(FANPIN, potSpeed);
  setPoints(0, 1); //Settato le soglie nel caso senza persone
  attachInterrupt(digitalPinToInterrupt(PIRPIN), checkPresence, CHANGE);

  //Setup del loop parallelo per stampare sullo schermo LCD
  Scheduler.startLoop(printOnLcd);

  //Setup del microfono della scheda
  PDM.onReceive(onPDMdata);
  if (!PDM.begin(1, 20000)) {
    Serial.println("Failed to start PDM!");
    while (1);
  }
}

void loop() {
  //Lettura dal sensore di temperatura e calcolo della temp in gradi celsius
  int V= analogRead(TEMPPIN);
  float R= (1023.0/(float)V -1.0)*R0; 
  T= (1.0/(log(R/R0)/B + (1.0/T0)))- 273.1;

  if(T >= minCond) //Caso in cui la T è tale da accendere la ventola
  {
    potSpeed= map(T, minCond, maxCond, 0, 255); //Più T è alto e più gira veloce
    analogWrite(FANPIN, potSpeed);
  }
  else if(T >= minHeat && T <=maxHeat) //caso in cui è tale da accendere la luce (per scaldare)
  {
    brightness= map(T, minHeat, maxHeat, 255, 0);//Più T è basso e più il led è luminoso
    analogWrite(RLED, brightness);
  }

  long int now=millis();
  if((now-lastTimeReadPir)> timeout_pir)//è passato molto tempo dall'ultimo movimento visto (persona presente)
  {
    numPeoplePir=0;
  }

  if((now-timeSoundEvents[lastPos]) >timeout_sound)
  {
    numPeopleMic=0;
  }

  if((numPeopleMic+ numPeoplePir) == 0) //Non ci sono persone neanche dietro al PIR
  {
    setPoints(0, 1);
  }

  if(Serial.available() > 0)
  {
    setPointsFromSerial();
  }

}

//Setup delle temperature di soglia (0, 1) senza persone e (2, 3) con persone
void setPoints(int min, int max)
{
  minCond=valCond[min];
  maxCond=valCond[max];
  minHeat=valHeat[min];
  maxHeat=valHeat[max];
}

void setPointsFromSerial()
{
  //Legge i valori dalla porta seriale tutti di fila
  float mAC= Serial.parseFloat();
  float MAC= Serial.parseFloat();
  float mHeat= Serial.parseFloat();
  float MHeat= Serial.parseFloat();

  setPointsSerial(mAC, MAC, mHeat, MHeat);
}

void setPointsSerial(float mAC, float MAC, float mHeat, float MHeat)
{
  minCond=mAC;
  maxCond=MAC;
  minHeat=mHeat;
  maxHeat=MHeat;
}

//ISR per il sensore PIR
void checkPresence()
{
  lastTimeReadPir=millis();
  numPeoplePir+=1;
  setPoints(2, 3); //caso con persone
}

//Funzione per la lettura dei dati nel microfono
void onPDMdata()
{
  int bytesAvailable= PDM.available();
  PDM.read(sampleBuffer, bytesAvailable);
  int samplesRead=bytesAvailable/2;

  for(int i=0; i<samplesRead; i++)
  {
    if(sampleBuffer[i] > sound_threshold)
    {
      lastPos= (lastPos+1)%n_sound_events;
      timeSoundEvents[lastPos]=millis();
      numSounds++;
      break;
    }
  }

  if((timeSoundEvents[lastPos]- timeSoundEvents[firstPos]) <= sound_interval && numSounds >= n_sound_events)
  {
    numPeopleMic++;
    numSounds--;
    firstPos= (firstPos+1)%n_sound_events; //Sposto l'indice del primo suono visto passando al successivo
    setPoints(2, 3);
  }
}

//Stampa in loop sullo schermo LCD cone ldue schermate che si alternano
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