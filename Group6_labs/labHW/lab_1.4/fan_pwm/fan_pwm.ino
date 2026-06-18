//Exercise 4 Lab 1: Fan with PWM
int RLED= 2;
int YLED= 3;
int PIRPIN= 7;
int FANPIN= 5;
volatile float speed=0;
volatile int potSpeed=0;

void setup() {
  Serial.begin(9600);
  while(!Serial);
  Serial.println("Exercise 4 Lab 1 DC Motor");
  pinMode(FANPIN, OUTPUT);
  analogWrite(FANPIN, potSpeed);
}

void loop() {
  if(Serial.available())
  {
    int in= Serial.read();
    char car = (char) in;
    if(car == '+')
    {
      if(potSpeed== 255)
       Serial.println("Already at maximum speed");
      else
      {
        speed= speed+10;
        potSpeed= map(speed, 0, 100, 0, 255);
        analogWrite(FANPIN, potSpeed);
      }
    }
    else if(car== '-')
    {
      if(potSpeed== 0)
       Serial.println("Already stopped");
      else
      {
        speed= speed-10;
        potSpeed= map(speed, 0, 100, 0, 255);
        analogWrite(FANPIN, potSpeed);
      }
    }
    else
    {
      Serial.println("Error, Invalid Character");
    }
  }
  Serial.print("Rotating at speed: ");
  Serial.println(analogRead(FANPIN));
}
