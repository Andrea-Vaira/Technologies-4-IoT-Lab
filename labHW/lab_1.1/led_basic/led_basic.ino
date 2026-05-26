//Exercise 1 Lab 1 
#include <MBED_RPi_Pico_TimerInterrupt.h>

const int RPIN= 2;
const int YPIN=3;
const long RPERIOD=1500L;
const long YPERIOD=3500L;
int stateR=LOW;
int stateY=LOW;
MBED_RPI_PICO_Timer ITimer1(1); //Initialize the timer

void blinkYellow(uint alarmNum)
{ 
  TIMER_ISR_START(alarmNum);//always needed in RP2040 for the ISR
  digitalWrite(YPIN, stateY);
  stateY= !stateY;
  TIMER_ISR_END(alarmNum); //End of the ISR
}

void setup() {
  pinMode(RPIN,OUTPUT);
  pinMode(YPIN,OUTPUT);
  ITimer1.setInterval(YPERIOD*1000, blinkYellow); //Every time the tier ends it invoke the blinkYellow ISR
}

void loop() {
  digitalWrite(RPIN, stateR); //Switch the red LED state
  stateR = !stateR;
  delay(RPERIOD);
}



