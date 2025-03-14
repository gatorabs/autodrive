#ifndef SERVO_CONTROL_H
#define SERVO_CONTROL_H

#include <Arduino.h>
#include <ESP32Servo.h>

#define SERVO_PIN 18

void setupServo();
void setServoAngle(int angle);

#endif
