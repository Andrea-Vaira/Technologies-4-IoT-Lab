//Exercise 1 Lab 1 Second Version with Scheduler 
#include <Scheduler.h>

const int RPIN= 2; 
const int YPIN=3;
const long RPERIOD=1500L;
const long YPERIOD=3500L;
int stateR=LOW;
int stateY=LOW;

void setup() {
  pinMode(RPIN,OUTPUT);
  pinMode(YPIN,OUTPUT);
  Scheduler.startLoop(parallelLoop);
}

void loop() {
  digitalWrite(RPIN, stateR); //Switch the red LED state
  stateR = !stateR;
  delay(RPERIOD);
}

void parallelLoop() //Parallel loop started with the Scheduler library
{
  digitalWrite(YPIN, stateY); //Switch the yellow LED state
  stateY = !stateY;
  delay(YPERIOD);
}
