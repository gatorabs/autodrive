#include <Servo.h>
#include "MotorController.h"
#include "CanController.h"
#include "BuzzerController.h"
#include "LightController.h"

#define LED_PIN 2
#define SERVO_PIN 33

MotorController motor1(6,7);
MotorController motor2(5,4);
MotorController motor3(8,9);
MotorController motor4(11,10);

CanController can;
BuzzerController buzzer;
LightController light;
Servo servo;

int idleServo = 87;

char canMessage = 'N'; 
bool obstacleDetected = false;

String inputString = "";
bool packetComplete = false;

int direction = 0;
int speedValue = 0;
int extraValue = 0;

void setup() {
  Serial.begin(115200);

  can.setup(53, 18);
  buzzer.setup();
  light.setup();

  motor1.begin();
  motor2.begin();
  motor3.begin();
  motor4.begin();

  servo.attach(SERVO_PIN);
  servo.write(idleServo);

  inputString.reserve(50);
}

void loop() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();

    if (inChar == '#') {
      packetComplete = true;
      break;
    } else {
      inputString += inChar;
    }
  }

  if (packetComplete) {
    parseAndExecute(inputString);
    inputString = "";
    packetComplete = false;
  }
}

void parseAndExecute(String data) {
  int values[3];
  int index = 0;
  char *token = strtok((char*)data.c_str(), ",");

  while (token != NULL && index < 3) {
    values[index++] = atoi(token);
    token = strtok(NULL, ",");
  }

  if (index == 3) {
    direction = values[0];
    speedValue = constrain(values[1], 0, 255);
    extraValue = values[2];

    mappedDirection = constrain(direction, 0, 180);  
    servo.write(mappedDirection); 

    canMessage = can.readCanMessage();

    if (canMessage == 'F') {
      obstacleDetected = true;
    } else {
      obstacleDetected = false;
    }

    if (obstacleDetected || speedValue == 0) {
      motor1.stop();
      motor2.stop();
      motor3.stop();
      motor4.stop();
      return;
    }
  }
}




