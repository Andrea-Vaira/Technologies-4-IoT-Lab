#include <Wire.h>
#include <LiquidCrystal_PCF8574.h>
#include <PDM.h>

// Pins
const int MOTOR_PIN = 5;
const int LED_PIN = 2;
const int MOV_PIN = 7;
const int TEMP_PIN = A0;

// LCD Setup
LiquidCrystal_PCF8574 lcd(0x27); 

// --- Constants & Thresholds ---
const int B = 4275; 
const long R0 = 100000;
const float T0 = 298.15;

const unsigned long TIMEOUT_PIR = 5000;    // 30 min
const unsigned long TIMEOUT_SOUND = 6000;  // 60 min
const unsigned long SOUND_WINDOW = 6000;   // 10 min window for events
const int N_SOUND_EVENTS = 10;
const int SOUND_THRESHOLD = 3000;

// --- Set-points (Requirement f) ---
// Structure: {AC_Min, AC_Max, Heat_Max, Heat_Min}
float sp_occ[4] = {25.0, 30.0, 20.0, 15.0};   // Occupied
float sp_unocc[4] = {28.0, 35.0, 15.0, 10.0}; // Unoccupied (Eco mode)

// --- State Variables ---
float temperatureC = 0.0;
int fanPct = 0;
int heatPct = 0;
volatile unsigned long lastPirMovement = 0;
unsigned long soundEvents[N_SOUND_EVENTS];
int soundIdx = 0;
unsigned long lastSoundTime = 0;
bool presence = false;

short sampleBuffer[256];
volatile int samplesRead = 0;
unsigned long lastLCDToggle = 0;
int lcdScreen = 0;

unsigned long lastClap = 0;

void setup() {
  Serial.begin(9600);
  pinMode(MOTOR_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  while(!Serial);
  pinMode(MOV_PIN, INPUT);
  
  lcd.begin(16, 2);
  lcd.setBacklight(255);

  attachInterrupt(digitalPinToInterrupt(MOV_PIN), sensorISR, RISING);
  PDM.onReceive(onPDMdata);
  if (!PDM.begin(1, 20000)) { while (1); }
  for (int i = 0; i < N_SOUND_EVENTS;i++){
    soundEvents[i] = 0;
  }
}

void loop() {
  unsigned long now = millis();
  // 1. Audio Processing
  if (samplesRead > 0) {
    for (int i = 0; i < samplesRead; i++) {
      if (abs(sampleBuffer[i]) > SOUND_THRESHOLD && now - lastClap > 1000) {
        registerSoundEvent(now);
        Serial.println(sampleBuffer[i]);
        lastClap = now;
        break; 
      }
    }
    
  }
  samplesRead = 0;

  // 2. Presence Logic (Requirement e)
  bool pirActive = (now - lastPirMovement < TIMEOUT_PIR);
  bool soundActive = checkSoundPresence(now);
  presence = pirActive || soundActive;

  // 3. Update Temperature & Controls
  updateTemperature();
  handleClimate(presence);

  // 4. Serial Command Parsing (Requirement h)
  // Format: "S[index][value]" e.g., "S0 26.5" updates Occupied AC Min
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'S') {
      int index = Serial.parseInt();
      float val = Serial.parseFloat();
      if (index >= 0 && index < 4) sp_occ[index] = val;
      Serial.println("Set-point Updated");
    }
  }

  // 5. LCD Management (Requirement g) - Toggle every 5s
  if (now - lastLCDToggle > 5000) {
    lcdScreen = (lcdScreen + 1) % 2;
    updateLCD();
    lastLCDToggle = now;
  }
}

void handleClimate(bool isPresent) {
  float* currentSP = isPresent ? sp_occ : sp_unocc;
  
  // AC Logic (Linear between sp[0] and sp[1])
  if (temperatureC >= currentSP[0]) {
    float raw = (temperatureC - currentSP[0]) / (currentSP[1] - currentSP[0]);
    fanPct = constrain(raw * 100, 0, 100);
  } else {
    fanPct = 0;
  }
  
  // Heater Logic (Linear between sp[2] and sp[3])
  if (temperatureC <= currentSP[2]) {
    float raw = (currentSP[2] - temperatureC) / (currentSP[2] - currentSP[3]);
    heatPct = constrain(raw * 100, 0, 100);
  } else {
    heatPct = 0;
  }

  //analogWrite(MOTOR_PIN, map(fanPct, 0, 100, 0, 255));
  analogWrite(LED_PIN, map(heatPct, 0, 100, 0, 255));
}

void updateLCD() {
  lcd.clear();
  if (lcdScreen == 0){
    lcd.setCursor(0,0);
    lcd.print("T:"); lcd.print(temperatureC, 1);
    lcd.print(" tipi?");
    lcd.print(presence ? "[Si]" : "[No]");
    lcd.setCursor(0,1);
    lcd.print("AC:"); lcd.print(fanPct); 
    lcd.print("% HT:"); lcd.print(heatPct); lcd.print("%");
  }else{
    float* s = presence ? sp_occ : sp_unocc;
    lcd.setCursor(0,0);
    lcd.print("AC:"); lcd.print(s[0],0); lcd.print("-"); lcd.print(s[1],0);
    lcd.setCursor(0,1);
    lcd.print("HT:"); lcd.print(s[2],0); lcd.print("-"); lcd.print(s[3],0);
  }
  
  
}

// --- Helpers ---
void sensorISR() { lastPirMovement = millis(); }

void onPDMdata() {
  int bytesAvailable = PDM.available();
  PDM.read(sampleBuffer, bytesAvailable);
  samplesRead = bytesAvailable / 2;
}

void registerSoundEvent(unsigned long now) {
  soundEvents[soundIdx] = now;
  soundIdx = (soundIdx + 1) % N_SOUND_EVENTS;
  lastSoundTime = now;
}

bool checkSoundPresence(unsigned long now) {
  // Check if we have 10 events within the 10-minute window
  int count = 0;
  for(int i=0; i<N_SOUND_EVENTS; i++) {
    if (now - soundEvents[i] < SOUND_WINDOW) count++;
  }
  Serial.print("Gente: ");
  Serial.println(count);
  static bool soundState = false;
  if (count >= N_SOUND_EVENTS) soundState = true;
  if (now - lastSoundTime > TIMEOUT_SOUND) soundState = false;
  return soundState;
}

void updateTemperature() {
  int val = analogRead(TEMP_PIN);
  float R = (1023.0 / (float)val - 1.0) * R0;
  temperatureC = 1.0 / (log(R / R0) / B + (1.0 / T0)) - 273.15;
}