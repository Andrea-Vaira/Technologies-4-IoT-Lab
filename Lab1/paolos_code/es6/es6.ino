#include <Wire.h>
#include <LiquidCrystal_PCF8574.h>

// I2C Address is usually 0x27 or 0x3F
LiquidCrystal_PCF8574 lcd(0x27); 

// Sensor Constants
const int B = 4275;               
const long R0 = 100000;           
const float T0 = 298.15;          
const int sensorPin = A0;         

void setup() {
  lcd.begin(16, 2);      // Initialize 16x2 LCD
  lcd.setBacklight(255); // Turn on backlight
  
  // Print static label once to minimize I2C traffic later
  lcd.setCursor(0, 0);
  lcd.print("Temp Monitor:");
  lcd.setCursor(0, 1);
  lcd.print("Value: ");
}

void loop() {
  // 1. Read and Calculate (Same logic as previous step)
  int val = analogRead(sensorPin);
  float R = (1023.0 / (float)val - 1.0) * R0;
  float temperatureK = 1.0 / (log(R / R0) / B + (1.0 / T0));
  float temperatureC = temperatureK - 273.15;

  // 2. Efficient LCD Update
  // We only move the cursor to the "Value: " position (column 7, row 1)
  lcd.setCursor(7, 1);
  
  // Overwrite only the numbers
  lcd.print(temperatureC);
  lcd.print((char)223); // Degree symbol
  lcd.print("C  ");      // Extra spaces clear old digits if value shrinks

  // Wait 10 seconds per specification
  delay(10000);
}