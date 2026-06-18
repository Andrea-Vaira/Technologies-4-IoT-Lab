//Exercise 3 Lab 1: PIR Sensor
const int LEDPIN= 2;
const int YLED=3;
const int PIRPIN = 7;
volatile int topCount=0;
long lastReport=0;
int interval= 30000;

void setup() {
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Ex 3 Lab 1: Pir Sensor");
  pinMode(LEDPIN, OUTPUT);
  pinMode(PIRPIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIRPIN), checkPresence, CHANGE); //For each status change it calls the ISR checkPresence
}

void loop() {
  long now = millis();
  if(now- lastReport >= interval)
  {
    Serial.print("Total People Count: ");
    Serial.println(topCount);
    lastReport=now;
  }
}

void checkPresence()
{
  int state= digitalRead(PIRPIN);
  if(state == HIGH)
    topCount++;

  digitalWrite(LEDPIN, state);
}
