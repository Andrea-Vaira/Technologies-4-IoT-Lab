// Pin Definition
int SENSOR_PIN = A0;

// Timing Configuration
unsigned long lastReadTime = 0;
unsigned long readInterval = 2000; // 10 seconds in milliseconds

void setup() {
  // Initialize serial communication at 9600 bits per second
  Serial.begin(9600);
  
  Serial.println("------------------------------------");
  Serial.println("Ambient Temperature Monitor Started");
  Serial.println("Interval: 10 Seconds");
  Serial.println("------------------------------------");
}

void loop() {
  unsigned long currentTime = millis();
  
  // Check if 10 seconds have passed
  
  if (currentTime - lastReadTime >= readInterval) {
    readTemperature();
    lastReadTime = currentTime;
  }
  
}

void readTemperature() {
  // 1. Read the raw ADC value (0 to 1023)
  int rawValue = analogRead(SENSOR_PIN);

  // 2. Convert raw value to voltage (assuming 5V Arduino like Uno/Mega)
  // Voltage = (ADC Value / 1024) * 5.0
  float voltage = (rawValue / 1024.0) * 5.0;

  // 3. Convert voltage to Celsius (Specific to TMP36)
  // TMP36 has a 500mV offset and 10mV per degree scale
  float temperatureC = (voltage - 0.5) * 100.0;

  // 4. Send the result to the PC
  Serial.print("Sensor Voltage: ");
  Serial.print(voltage);
  Serial.print("V | ");
  Serial.print("Temperature: ");
  Serial.print(temperatureC);
  Serial.println(" °C");
}