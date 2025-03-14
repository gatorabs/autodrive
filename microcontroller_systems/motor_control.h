#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

#include <Arduino.h> 

#define RPM_A 32
#define RPM_B 14

#define IN1 33
#define IN2 25
#define IN3 27
#define IN4 26

void setupMotors();
void motor_control(int m1_a, int m1_b, int m2_a, int m2_b, int speedA, int speedB);
void setMotorSpeed(int motorA_speed, int motorB_speed);

#endif
