#include <Servo.h>
#include "MotorController.h"
#include "BuzzerController.h"
#include "LightController.h"

#define LED_PIN 13
#define SERVO_PIN 33
#define SERIAL_TIMEOUT_MS 1000  // Tempo máximo sem comunicação

MotorController motors[] = {
  MotorController(6, 7),
  MotorController(5, 4),
  MotorController(8, 9),
  MotorController(11, 10)
};

BuzzerController buzzer;
LightController light;
Servo servo;

int idleServo = 87;
int direction = 0;
int speedValue = 0;
int extraValue = 0;
bool obstacleDetected = false;

unsigned long lastSerialTime = 0; // Guarda o último momento de comunicação

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  buzzer.setup();
  light.setup();
  for (int i = 0; i < 4; i++) motors[i].begin();

  servo.attach(SERVO_PIN);
  servo.write(idleServo);
  lastSerialTime = millis();
}

void loop() {
  static char buf[50];

  size_t len = Serial.readBytesUntil('#', buf, sizeof(buf) - 1);
  if (len > 0) {
    buf[len] = '\0';
    parseAndExecute(buf);
    lastSerialTime = millis(); // Atualiza tempo quando nova mensagem chega
  }

  // Verifica timeout de comunicação
  if (millis() - lastSerialTime > SERIAL_TIMEOUT_MS) {
    stopMotorsForSafety();
  }
}

void stopMotorsForSafety() {
  digitalWrite(LED_PIN, HIGH);
  for (int i = 0; i < 4; i++) {
    motors[i].stop();
  }
}

void parseAndExecute(char *data) {
  int values[3];
  int idx = 0;

  char *token = strtok(data, ",");
  while (token != nullptr && idx < 3) {
    values[idx++] = atoi(token);
    token = strtok(nullptr, ",");
  }

  if (idx != 3) return;

  direction  = constrain(values[0], 0, 180);
  speedValue = constrain(values[1], 0, 255);
  extraValue = values[2];

  servo.write(direction);

  if (obstacleDetected || speedValue == 0) {
    stopMotorsForSafety();
    return;
  }

  digitalWrite(LED_PIN, LOW);
  for (int i = 0; i < 4; i++) {
    motors[i].turnFront(speedValue);
  }
}
