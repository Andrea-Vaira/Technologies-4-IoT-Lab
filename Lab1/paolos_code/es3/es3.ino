// Pin Definitions
const int PIR_PIN = 2;    // Must be an interrupt-capable pin (2 or 3 on Uno/Nano)
const int LED_PIN = 13;   // Internal LED or external LED with resistor

// Volatile variables are necessary for data shared between ISR and Main Loop
volatile int eventCounter = 0;
volatile bool motionState = false;

// Timing variables
unsigned long lastReportTime = 0;
const unsigned long reportInterval = 30000; // 30 seconds in milliseconds

void setup() {
  pinMode(PIR_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  
  Serial.begin(9600);
  
  // Attach interrupt to the PIR pin
  // Triggered on CHANGE (both rising and falling edges)
  attachInterrupt(digitalPinToInterrupt(PIR_PIN), sensorISR, CHANGE);
  
  Serial.println("System Initialized. Monitoring motion...");
}

void loop() {
  unsigned long currentTime = millis();

  // Send report every 30 seconds
  if (currentTime - lastReportTime >= reportInterval) {
    Serial.print("Total events detected: ");
    Serial.println(eventCounter);
    
    lastReportTime = currentTime;
  }
}

// Interrupt Service Routine (ISR)
void sensorISR() {
  // Read the current state of the PIR sensor
  int sensorValue = digitalRead(PIR_PIN);
  
  // Reproduce sensor value on the LED
  digitalWrite(LED_PIN, sensorValue);
  
  // Count an event only on the RISING edge (transition from LOW to HIGH)
  // This ensures we count one "person" per detection cycle
  if (sensorValue == HIGH) {
    eventCounter++;
  }
}