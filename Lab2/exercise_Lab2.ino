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
volatile int numPeople=0;
const int timeout_pir= 1000*60*30; //30 minuti
volatile long int timeReadPir=0;
const int n_soud_events=10;

void setup() {
  //Serial.begin(9600);
  //while(!Serial);
  //Serial.println("Exercise Lab 2: Local Smart Home");
  lcd.begin(16, 2);
  lcd.setBacklight(255);
  lcd.home();
  lcd.clear();
  pinMode(RLED, OUTPUT);
  pinMode(TEMPPIN, INPUT);
  pinMode(FANPIN, OUTPUT);
  digitalWrite(FANPIN, potSpeed);
  minCond=22;
  maxCond=30;
  minHeat=15;
  maxHeat=25;
  Scheduler.startLoop(printOnLcd);
  attachInterrupt(digitalPinToInterrupt(PIRPIN), checkPresence, CHANGE);
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
  if((now-timeReadPir)> timeout_pir)
  {
    numPeople=0;
  }

}

void checkPresence()
{
  timeReadPir=millis();
  numPeople+=1;
}

void printOnLcd()
{
  lcd.print("T: ");
  lcd.print(T);
  lcd.print("Pres: ");
  lcd.print(numPeople);
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
