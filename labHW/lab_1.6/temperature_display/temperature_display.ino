//Exercise 6 Lab 1 Tmperature Sensor with LCD Display
#include <LiquidCrystal_PCF8574.h>
int RLED= 2; 
int YLED= 3;
int PIRPIN= 7;
int FANPIN= 5; 
int TEMPPIN = A0; //21
const int B=4275;
const long int R0=100000;
const int T0= 298.13;

//PIN needed for SDA and SCL are A4 ed A5
LiquidCrystal_PCF8574 lcd(0x27); //0x27 it is the memory area of the display

void setup() {
  lcd.begin(16, 2);
  lcd.setBacklight(50);
  lcd.home();
  lcd.clear();
  lcd.print("Temperature:");
  pinMode(TEMPPIN, INPUT);
}

void loop() {
  int V= analogRead(TEMPPIN); //Read the Voltage
  double R= (1023.0/V -1.0)*R0; //R1=R0
  float T= 1.0/(log(R/R0)/B + 1.0/T0)-273.15; 
  lcd.setCursor(12, 0); //Set the cursor after the write "Temperature:"
  lcd.print(T); //Write the temperature
  lcd.print("   ");
  delay(2000); //10 seconds
}