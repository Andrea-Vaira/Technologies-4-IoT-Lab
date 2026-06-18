//Exercise 1 Lab 1 Third Version witn Scheduler and Internal Led
#include <Scheduler.h>
#include <WiFiNINA.h>

const int RPIN= 2; 
const int YPIN=3;
const long RPERIOD=1500L;
const long YPERIOD=3500L;
int stateR=LOW;
int stateY=LOW;
int stateInternalPin = LOW;

void setup() {
  pinMode(RPIN,OUTPUT);
  pinMode(YPIN,OUTPUT);
  Scheduler.startLoop(parallelLoop);
}

void loop() {
  digitalWrite(RPIN, stateR); //Switch the red LED state
  digitalWrite(LEDR, (PinStatus) stateInternalPin);
  stateInternalPin= !stateInternalPin;
  stateR = !stateR;
  delay(RPERIOD);
}

void parallelLoop() //Parallel Loop
{
  digitalWrite(YPIN, stateY); //Switch the red LED state
  stateY = !stateY;
  delay(YPERIOD);
}
