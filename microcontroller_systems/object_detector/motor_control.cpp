#include "motor_control.h"

void setupMotors() {
  pinMode(RPM_A, OUTPUT);
  pinMode(RPM_B, OUTPUT);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  analogWrite(RPM_A, 0);
  analogWrite(RPM_B, 0);
}

void motor_control(int m1_a, int m1_b, int m2_a, int m2_b, int speedA, int speedB) {  
  digitalWrite(IN1, m1_a);
  digitalWrite(IN2, m1_b);

  digitalWrite(IN3, m2_a);
  digitalWrite(IN4, m2_b);

  setMotorSpeed(speedA, speedB);
}

void setMotorSpeed(int motorA_speed, int motorB_speed) {
  analogWrite(RPM_A, motorA_speed);
  analogWrite(RPM_B, motorB_speed);
}
