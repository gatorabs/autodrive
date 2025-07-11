#include <Servo.h>
#include "MotorController.h"
#include "CanController.h"
#include "BuzzerController.h"
#include "LightController.h"

#define LED_PIN 13
#define SERVO_PIN 33

MotorController motors[] = {
  MotorController(6, 7),
  MotorController(5, 4),
  MotorController(8, 9),
  MotorController(11, 10)
};

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

  pinMode(LED_PIN, OUTPUT);

  bool canOK = can.setup(53, 18);
  if (!canOK) {
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }

  digitalWrite(LED_PIN, LOW);
  buzzer.setup();
  light.setup();

  for (int i = 0; i < 4; i++) {
    motors[i].begin();
  }

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

    int mappedDirection = constrain(direction, 0, 180);  
    servo.write(mappedDirection); 

    //canMessage = can.readCanMessage();
    //obstacleDetected = (canMessage == 'F');

    if (obstacleDetected || speedValue == 0) {
      digitalWrite(LED_PIN, HIGH);  
      for (int i = 0; i < 4; i++) {
        motors[i].stop();
      }
      return;
    }


    digitalWrite(LED_PIN, LOW);

    for (int i = 0; i < 4; i++) {
      motors[i].turnFront(speedValue);
    }
  }
}
