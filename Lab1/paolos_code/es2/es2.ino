const  int LED_PIN = 2;
const int PIR_PIN = 4;

volatile int tot_count = 0;
volatile bool sensorState = LOW;

unsigned long lastReportTime = 0;
const unsigned long reportInterval = 30000; // 30 seconds in milliseconds

void checkPresence() {
  // Read current sensor state
  sensorState = digitalRead(PIR_PIN);
  
  // Reproduce state on the LED
  digitalWrite(LED_PIN, sensorState);
  
  // Define an 'event' as the start of a new movement (Rising Edge)
  if (sensorState == HIGH) {
    tot_count++;
  }
}

void setup() {
  pinMode(PIR_PIN,INPUT);
  pinMode(LED_PIN,OUTPUT);
  attachInterrupt(digitalPinToInterrupt(PIR_PIN),checkPresence,CHANGE);
  Serial.println("System Initialized. Monitoring motion...");
}

void loop() {
  unsigned long currentTime = millis();

  // Check if 30 seconds have passed
  if (currentTime - lastReportTime >= reportInterval) {
    Serial.print("Total events detected in the last interval: ");
    Serial.println(tot_count);
    
    lastReportTime = currentTime;
  }
}



