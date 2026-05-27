//Exercise 2 Lab 1 starting from exercise 1.2 we add Serial Interaction 
#include <Scheduler.h>
const int RPIN= 2; 
const int YPIN=3;
const long RPERIOD=1500L;
const long YPERIOD=3500L;
int stateR=LOW;
int stateY=LOW;

void setup() {
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Welcome to Exercise 2 Lab 1: Serial Ports");
  pinMode(RPIN,OUTPUT);
  pinMode(YPIN,OUTPUT);
  Scheduler.startLoop(parallelLoop);
}

void loop() {
  digitalWrite(RPIN, stateR);
  stateR = !stateR;
  delay(RPERIOD);
  serialPrintStatus();
}

void parallelLoop() //Parallel loop created with scheduler used to change the Yellow LED State
{
  digitalWrite(YPIN, stateY); 
  stateY = !stateY;
  delay(YPERIOD);
  serialPrintStatus();
}

void serialPrintStatus()
{
  if(Serial.available() > 0) //Check for incoming bytes
  {
    char car= (char) Serial.read(); //Read the single byte
    if(car == 'R' || car == 'r')
    {
      Serial.print("LED 2 (Red) Status: ");
      Serial.println(stateR);
    }
    else if(car == 'Y' || car=='y')
    {
      Serial.print("LED 3 (Yellow) Status: ");
      Serial.println(stateY);
    }
    else
    {
      Serial.println("Error: wrong character");
    }
  }
}