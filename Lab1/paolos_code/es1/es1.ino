#include <MBED_RPi_Pico_TimerInterrupt.h>

const int RLED_PIN = 2;
const int YLED_PIN = 3;

const long R_HALF_PERIOD = 1500L;
const long Y_HALF_PERIOD = 3500L;

int redLedState = LOW;
int yellowLedState = LOW;

MBED_RPI_PICO_Timer ITimer1(1);

void blinkYellow(uint alarm_num){
  TIMER_ISR_START(alarm_num);
  digitalWrite(YLED_PIN,yellowLedState);
  yellowLedState = !yellowLedState;
  TIMER_ISR_END(alarm_num);
}


void setup() {
  // put your setup code here, to run once:
  pinMode(RLED_PIN,OUTPUT);
  pinMode(YLED_PIN,OUTPUT);
  ITimer1.setInterval(Y_HALF_PERIOD * 1000,blinkYellow);
}

void loop() {
  // put your main code here, to run repeatedly:
  digitalWrite(RLED_PIN,redLedState);
  redLedState = !redLedState;
  delay(R_HALF_PERIOD);
}

