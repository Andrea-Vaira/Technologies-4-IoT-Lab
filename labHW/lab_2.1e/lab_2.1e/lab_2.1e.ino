//Exercise Lab 2 : Local Smart Home
#include <LiquidCrystal_PCF8574.h>
#include <Scheduler.h>
#include <MBED_RPi_Pico_TimerInterrupt.h>
#include <PDM.h>

int RLED= 2; 
int YLED= 3;
int GLED= 4;
int PIRPIN= 7;
int FANPIN= 5; 
int TEMPPIN = A0; //14

const int B=4275;
const long int R0=100000;
const int T0= 298.13;
volatile float T=0.0;
int potSpeed=0;
int brightness=0;
LiquidCrystal_PCF8574 lcd(0x27); 

volatile int minHeat; //Temperature for Heating LED
volatile int maxHeat;
volatile int minCond; //temperature for Air Conditioning FAN
volatile int maxCond;

const int valHeat[]={15, 20, 10, 15};
const int valCond[]={25, 30, 20, 25};

volatile int numPeoplePir=0; 

//volatile int numPeopleMic=0; //Not needed for bonus

const int timeout_pir= 1000*60*2; //2 minutes
volatile long int lastTimeReadPir=0;

const int n_sound_events=10;
const int sound_interval= 1000*60*1;//1 minutes
const int sound_threshold=1500;
const int timeout_sound=1000*60*1; //1 minutes
volatile int timeSoundEvents[n_sound_events]; //Buffer for times for michrophone events
volatile int firstPos=0; //Indexes for the buffer 
volatile int lastPos=-1; //starts from -1 so that at the first reading is placed at 0
short sampleBuffer[512];
volatile int numSounds=0;

//Added variables
volatile bool greenLedState = false;
volatile unsigned long lastClapTime = 0;
volatile int clapCount = 0;
const int clapAmplitudeThresholdmin = 3000;
const int clapAmplitudeThresholdmax = 4000;
const unsigned long minClapInterval = 200; 
const unsigned long maxClapInterval = 1000; 


void setup() {
  //Setup Serial Port
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Exercise Lab 2e: Local Smart Home");
  Serial.println("To set the thresholds for temperatures write them as:  minAC maxAC minHeat maxHeat (one after the other only with one space)");
  //Setup of LCD Display
  lcd.begin(16, 2);
  lcd.setBacklight(255);
  lcd.home();
  lcd.clear();

  //Setup of the pins for LED, Temperature Sensor, FAN and PIR sensor
  pinMode(RLED, OUTPUT);
  pinMode(GLED, OUTPUT);
  digitalWrite(GLED, LOW);
  pinMode(TEMPPIN, INPUT);
  pinMode(FANPIN, OUTPUT);
  digitalWrite(FANPIN, potSpeed);
  setPoints(0, 1); //Set the thresholds for the case without any people
  attachInterrupt(digitalPinToInterrupt(PIRPIN), checkPresence, CHANGE);

  //Setup fot he parallel loop to print on the LCD Display
  Scheduler.startLoop(printOnLcd);

  //Setup of the michrophone of the board
  PDM.onReceive(onPDMdata);
  if (!PDM.begin(1, 20000)) {
    Serial.println("Failed to start PDM!");
    while (1);
  }
}

void loop() {
  //Read of the voltage and formulas to get the value in Celsius
  int V= analogRead(TEMPPIN);
  float R= (1023.0/(float)V -1.0)*R0; 
  T= (1.0/(log(R/R0)/B + (1.0/T0)))- 273.1;

  if(T >= minCond) //If T can start the FAN
  {
    potSpeed= map(T, minCond, maxCond, 0, 255); //With higher T the FAN rotate more rapidly
    analogWrite(FANPIN, potSpeed);
  }
  else if(T >= minHeat && T <=maxHeat) //Low T, the LED is used to heat the room
  {
    brightness= map(T, minHeat, maxHeat, 255, 0);//The LED is more bright as the temperature is lower
    analogWrite(RLED, brightness);
  }

  long int now=millis();
  if((now-lastTimeReadPir)> timeout_pir)//Its passed too much time from the last person seen
  {
    numPeoplePir=0;
  }

  /* Not needed for bonus
  if((now-timeSoundEvents[lastPos]) >timeout_sound)//No people heard fo too much time
  {
    numPeopleMic=0;
  }



  if((numPeopleMic+ numPeoplePir) == 0) //No people present
  {
    setPoints(0, 1);
  }
  */
  if (numPeoplePir == 0)
  {
    setPoints(0, 1);
    if (greenLedState)
    {
      greenLedState = false;
      digitalWrite(GLED, LOW);
    }
  }


  if(Serial.available() > 0)
  {
    setPointsFromSerial();
  }


}

//Setup of temperature thresholds: (0, 1) without people and (2, 3) with people
void setPoints(int min, int max)
{
  minCond=valCond[min];
  maxCond=valCond[max];
  minHeat=valHeat[min];
  maxHeat=valHeat[max];
}

void setPointsFromSerial()
{
  //Read the values from the Serial Port all together
  float mAC= Serial.parseFloat();
  float MAC= Serial.parseFloat();
  float mHeat= Serial.parseFloat();
  float MHeat= Serial.parseFloat();

  setPointsSerial(mAC, MAC, mHeat, MHeat);
}

void setPointsSerial(float mAC, float MAC, float mHeat, float MHeat)
{
  minCond=mAC;
  maxCond=MAC;
  minHeat=mHeat;
  maxHeat=MHeat;
}

//ISR for PIR sensor
void checkPresence()
{
  lastTimeReadPir=millis();
  numPeoplePir+=1;
  setPoints(2, 3); //case with people
}

//Function for the read of the data from the michropohone
void onPDMdata()
{
  int bytesAvailable= PDM.available();
  PDM.read(sampleBuffer, bytesAvailable);
  int samplesRead=bytesAvailable/2;

  /* Not needed for bonus
  for(int i=0; i<samplesRead; i++)
  {
    if(sampleBuffer[i] > sound_threshold)
    {
      lastPos= (lastPos+1)%n_sound_events;
      timeSoundEvents[lastPos]=millis();
      numSounds++;
      break;
    }
  }

  if((timeSoundEvents[lastPos]- timeSoundEvents[firstPos]) <= sound_interval && numSounds >= n_sound_events)
  {
    numPeopleMic++;
    numSounds--;
    firstPos= (firstPos+1)%n_sound_events; //Shift the index to the next sound heard
    setPoints(2, 3);
  }
  */
  int maxAmplitude = 0;

  for (int i = 0; i < samplesRead; i++) 
  {
    int currentAmplitude = abs(sampleBuffer[i]);
  
    if (currentAmplitude > maxAmplitude) 
    {
      maxAmplitude = currentAmplitude;
    }
  }

  if (maxAmplitude > clapAmplitudeThresholdmin && maxAmplitude < clapAmplitudeThresholdmax )
    {
    unsigned long now = millis();
    unsigned long timeSinceLastClap = now - lastClapTime;
    if (timeSinceLastClap > maxClapInterval) 
    {
      clapCount = 1;
      lastClapTime = now;
    }
    else if (timeSinceLastClap > minClapInterval) 
    {
      clapCount++;
      lastClapTime = now;
      if (clapCount >= 2)
      {
        greenLedState = !greenLedState;
        digitalWrite(GLED, greenLedState ? HIGH : LOW);
        clapCount = 0;
      }
    }
  }
}

//In a loop, function to print on the LCD Display
void printOnLcd()
{
  //int numPeople=numPeoplePir+ numPeopleMic;
  int numPeople = numPeoplePir;
  lcd.print("T: ");
  lcd.print(T);
  lcd.print("P:");
  lcd.print(numPeople);
  lcd.setCursor(0,1);
  lcd.print("AC: ");
  lcd.print(potSpeed);
  lcd.print(" HT: ");
  lcd.print(brightness);
  lcd.print(" ");
  delay(5*1000);
  lcd.setCursor(1,0);
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("AC m:");
  lcd.print(minCond);
  lcd.print(" M:");
  lcd.print(maxCond);
  lcd.setCursor(0,1);
  lcd.print("HT m:");
  lcd.print(minHeat);
  lcd.print(" M:");
  lcd.print(maxHeat);
  delay(5*1000);
  lcd.setCursor(1,0);
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.clear();
  lcd.setCursor(0,0);
}