//Exercise 5 Lab 1: Temperature Sensor
int RLED= 2;
int YLED= 3;
int PIRPIN= 7;
int FANPIN= A1; //15
int TEMPPIN = A0; //14
const int B=4275;
const long int R0=100000;
const int T0= 25;

void setup() {
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Exercize 5 Lab 1 Temperature Sensor");
  pinMode(TEMPPIN, INPUT);
}

void loop() {
  int n= analogRead(TEMPPIN); //Read the voltage from the sensor
  double R= (1023/n -1)*R0; //R1=R0 from the data in the slides
  double T= 1/(log(R/R0)/B + 1/T0) -273.1;
  Serial.print("Temperature: ");
  Serial.println(T);
  delay(10000); //10 seconds
}