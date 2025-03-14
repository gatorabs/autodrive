#include "servo_control.h"

Servo myServo;

void setupServo() {
  myServo.attach(SERVO_PIN);
}

void setServoAngle(int angle) {

  angle = map(angle, -32, 32, 90, 180);
  myServo.write(angle);
}
