// Pin Definition - Must be a PWM pin (3, 5, 6, 9, 10, or 11 on Uno)
const int MOTOR_PIN = 5;

// Speed Configuration
const int NUM_STEPS = 10;
const int STEP_SIZE = 255 / NUM_STEPS; // approx 25.5 per step

int currentStep = 0; // Starts at 0 (Off)

void setup() {
  pinMode(MOTOR_PIN, OUTPUT);
  
  // Specification: Set rotation speed to 0 initially
  analogWrite(MOTOR_PIN, 0);
  
  Serial.begin(9600);
  Serial.println("Fan Control System Initialized.");
  Serial.println("Use '+' to increase, '-' to decrease speed.");
}

void loop() {
  if (Serial.available() > 0) {
    char input = Serial.read();
    
    // Ignore newline or carriage return characters from Serial Monitor
    if (input == '\n' || input == '\r') return;

    if (input == '+') {
      increaseSpeed();
    } 
    else if (input == '-') {
      decreaseSpeed();
    } 
    else {
      Serial.print("Error: Invalid character '");
      Serial.print(input);
      Serial.println("'. Use '+' or '-' only.");
    }
  }
}

void increaseSpeed() {
  if (currentStep < NUM_STEPS) {
    currentStep++;
    updateMotor();
  } else {
    Serial.println("Warning: Maximum speed already reached!");
  }
}

void decreaseSpeed() {
  if (currentStep > 0) {
    currentStep--;
    updateMotor();
  } else {
    Serial.println("Warning: Minimum speed (Off) already reached!");
  }
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