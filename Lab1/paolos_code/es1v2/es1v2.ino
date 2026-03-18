#include <Scheduler.h>

const int RLED_PIN = 2;
const int YLED_PIN = 3;

const long R_HALF_PERIOD = 1500L;
const long Y_HALF_PERIOD = 3500L;

int redLedState = LOW;
int yellowLedState = LOW;


void setup() {
  pinMode(RLED_PIN,OUTPUT);
  pinMode(YLED_PIN,OUTPUT);
  Scheduler.startLoop(loop2);
}

void loop() {
  digitalWrite(RLED_PIN,redLedState);
  redLedState = !redLedState;
  delay(R_HALF_PERIOD);
}

void loop2() {
  digitalWrite(YLED_PIN,yellowLedState);
  yellowLedState = !yellowLedState;
  delay(Y_HALF_PERIOD);
}
