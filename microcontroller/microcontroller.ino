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
int direction = 0;
int speedValue = 0;
int extraValue = 0;
bool obstacleDetected = false;

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  if (!can.setup(53, 18)) {
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }

  buzzer.setup();
  light.setup();
  for (int i = 0; i < 4; i++) {
    motors[i].begin();
  }

  servo.attach(SERVO_PIN);
  servo.write(idleServo);
}

void loop() {
  // Buffer fixo onde será lido até o caractere '#'
  static char buf[50];
  size_t len = Serial.readBytesUntil('#', buf, sizeof(buf) - 1);
  if (len == 0) return;    // nada novo chegou

  buf[len] = '\0';         // marca fim da string
  parseAndExecute(buf);
}

void parseAndExecute(char *data) {
  int values[3];
  int idx = 0;

  // tokenização segura em buffer mutável
  char *token = strtok(data, ",");
  while (token != nullptr && idx < 3) {
    values[idx++] = atoi(token);
    token = strtok(nullptr, ",");
  }

  // se não vieram exatamente 3 valores, aborta
  if (idx != 3) return;

  direction  = constrain(values[0], 0, 180);
  speedValue = constrain(values[1], 0, 255);
  extraValue = values[2];

  servo.write(direction);

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
