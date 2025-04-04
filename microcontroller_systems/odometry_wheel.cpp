#include "odometry_wheel.h"
#include "odometry_wheel.h"

#define encoder1APin 2
#define encoder1BPin 3
#define encoder2APin 4
#define encoder2BPin 5

const int pulsesPerRevolution = 360;
const float wheelRadiusCm = 5.0; // Replace with the actual radius of your wheels in centimeters

volatile long encoder1Ticks = 0;
volatile long encoder2Ticks = 0;

long previousEncoder1Ticks = 0;
long previousEncoder2Ticks = 0;

unsigned long previousTime = 0;
unsigned long timeInterval = 100;

unsigned long currentTime;

void encoder1A_ISR() {
  if (digitalRead(encoder1BPin) == LOW) {
    encoder1Ticks++;
  } else {
    encoder1Ticks--;
  }
}

void encoder1B_ISR() {
  if (digitalRead(encoder1APin) == HIGH) {
    encoder1Ticks++;
  } else {
    encoder1Ticks--;
  }
}

void encoder2A_ISR() {
  if (digitalRead(encoder2BPin) == LOW) {
    encoder2Ticks++;
  } else {
    encoder2Ticks--;
  }
}

void encoder2B_ISR() {
  if (digitalRead(encoder2APin) == HIGH) {
    encoder2Ticks++;
  } else {
    encoder2Ticks--;
  }
}


void setup_encoder(){
  pinMode(encoder1APin, INPUT_PULLUP); // Use internal pull-up resistor
  pinMode(encoder1BPin, INPUT_PULLUP); 
  pinMode(encoder2APin, INPUT_PULLUP); 
  pinMode(encoder2BPin, INPUT_PULLUP); 

  // Attach interrupts for encoder 1 (using CHANGE for full quadrature decoding)
  attachInterrupt(digitalPinToInterrupt(encoder1APin), encoder1A_ISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(encoder1BPin), encoder1B_ISR, CHANGE);

  attachInterrupt(digitalPinToInterrupt(encoder2APin), encoder2A_ISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(encoder2BPin), encoder2B_ISR, CHANGE);
}


void loop_encoder(){
  currentTime = millis();
  if (currentTime - previousTime >= timeInterval) {
    // Disable interrupts while reading encoder ticks to ensure atomic read
    noInterrupts();
    long currentEncoder1Ticks = encoder1Ticks;
    long currentEncoder2Ticks = encoder2Ticks;
    interrupts();

    // Calculate ticks per interval for each encoder
    long ticks1PerInterval = currentEncoder1Ticks - previousEncoder1Ticks;
    long ticks2PerInterval = currentEncoder2Ticks - previousEncoder2Ticks;

    // Calculate distance traveled per tick (considering quadrature encoding)
    float distancePerTick = (2.0 * PI * wheelRadiusCm) / (pulsesPerRevolution * 4.0);

    // Calculate linear distance traveled in cm for each wheel
    float distance1Cm = ticks1PerInterval * distancePerTick;
    float distance2Cm = ticks2PerInterval * distancePerTick;

    // Calculate time interval in seconds
    float timeIntervalSec = (float)timeInterval / 1000.0;

    // Calculate linear speed in cm/s for each wheel
    float speed1CmPerS = distance1Cm / timeIntervalSec;
    float speed2CmPerS = distance2Cm / timeIntervalSec;

    Serial.print("Wheel 1 Speed: ");
    Serial.print(speed1CmPerS);
    Serial.println(" cm/s");

    Serial.print("Wheel 2 Speed: ");
    Serial.print(speed2CmPerS);
    Serial.println(" cm/s");
    Serial.println("--------------------");

    previousTime = currentTime;
    previousEncoder1Ticks = currentEncoder1Ticks;
    previousEncoder2Ticks = currentEncoder2Ticks;
  }
}