#include "Arduino.h"
#include "MotorController.h"

 MotorController::MotorController(int RPWM,int LPWM)
{
    this->RPWM = RPWM;
    this->LPWM = LPWM;
}

void MotorController::begin() {
    pinMode(RPWM, OUTPUT);
    pinMode(LPWM, OUTPUT);
}

void MotorController::turnBack(int vel)
{
  analogWrite(RPWM,vel);
}

void MotorController::turnFront(int vel)
{
  analogWrite(LPWM,vel);
}

void MotorController::stop() {
    analogWrite(RPWM, 0);
    analogWrite(LPWM, 0);
}