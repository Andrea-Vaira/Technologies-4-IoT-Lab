
#include <Wire.h>
#include <LiquidCrystal_PCF8574.h>

const int MOTOR_PIN = 5;
const int LED_PIN = 2;
const int MOV_PIN = 7;

const int NUM_STEPS = 10;
const int NUM_STEPS_LED = 5;

const int STEP_SIZE = 255 / NUM_STEPS; // approx 25.5 per step
const int STEP_SIZE_LED = 255 / NUM_STEPS_LED; // approx 25.5 per step

int currentStep = 0; // Starts at 0 (Off)
int currentStepLED = 0;

// Sensor Constants
const int B = 4275;               
const long R0 = 100000;           
const float T0 = 298.15;          
const int sensorPin = A0;  

volatile int eventCounter = 0;
volatile int lasteventCounter = 0;
volatile bool sensorState = LOW;

const int timeout_pir = 20000;
unsigned long lastReportTimePeople = 0;
unsigned long lastReportTime = 0;
const unsigned long reportInterval = 8000; // 30 seconds in milliseconds


void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  Serial.println("roba");
  attachInterrupt(digitalPinToInterrupt(MOV_PIN), sensorISR, CHANGE);
  
}



void loop() {
  unsigned long currentTime = millis();
  if (currentTime - lastReportTime >= reportInterval) {
    if (currentTime - lastReportTimePeople >= timeout_pir){
      if (lasteventCounter == eventCounter){
        eventCounter = 0;
      }
      lasteventCounter = eventCounter;
      lastReportTimePeople = currentTime;
    }
    // 1. Read and Calculate 
    int val = analogRead(sensorPin);
    float R = (1023.0 / (float)val - 1.0) * R0;
    float temperatureK = 1.0 / (log(R / R0) / B + (1.0 / T0));
    float temperatureC = temperatureK - 273.15;

    Serial.print("Fa caldo: ");
    Serial.println(temperatureC);
    Serial.print("Gente: ");
    Serial.println(eventCounter);

    if (temperatureC >= 25){
      currentStep = 35-temperatureC;
      if (currentStep > 10) currentStep = 10;
    }else{
      currentStep = 0;
    }
    //updateMotor();

    if (temperatureC >= 15){
      currentStepLED = 20-temperatureC;
      if (currentStepLED < 0) currentStepLED = 0;
    }else{
      currentStepLED = 0;
    }
    updateLED();
    

    writeLCD();
    lastReportTime = currentTime;
  }

}

void updateLED(){
  int brightness = currentStepLED * STEP_SIZE_LED;
  if (currentStepLED == NUM_STEPS_LED) brightness = 255;

  analogWrite(LED_PIN, brightness);
  Serial.print("brightness Step: ");
  Serial.print(currentStepLED);
  Serial.print("/");
  Serial.print(NUM_STEPS_LED);
  Serial.print(" (brightness Value: ");
  Serial.print(brightness);
  Serial.println(")");
}


void updateMotor() {
  // Calculate PWM value (0-255)
  int pwmValue = currentStep * STEP_SIZE;
  
  // Ensure the 10th step hits exactly 255 (100% duty cycle)
  if (currentStep == NUM_STEPS) pwmValue = 255;

  analogWrite(MOTOR_PIN, pwmValue);
  
  // Feedback to user
  Serial.print("Speed Step: ");
  Serial.print(currentStep);
  Serial.print("/");
  Serial.print(NUM_STEPS);
  Serial.print(" (PWM Value: ");
  Serial.print(pwmValue);
  Serial.println(")");
}

void sensorISR() {
  
  int sensorValue = digitalRead(MOV_PIN);
  if (sensorValue == HIGH) {
    eventCounter++;
  }
  
}

void writeLCD(){
  lcd.setCursor(0,0);
  lcd.clear();
  lcd.setCursor(1,0);
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("T:");
  lcd.print(temperatureC);
  lcd.print("F:");
  lcd.print(100/currentStep);
  lcd.setCursor(1,0);
  lcd.print("P:");
  lcd.print(eventCounter);
  delay(5*1000);
  lcd.setCursor(0,0);
  lcd.clear();
  lcd.setCursor(1,0);
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("A:");
  lcd.print(temperatureC);
  lcd.print("R:");
  lcd.print(100/currentStep);
  lcd.setCursor(1,0);
  lcd.print("F:");
  lcd.print(eventCounter);
  delay(5*1000);
}
