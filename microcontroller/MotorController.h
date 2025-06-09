#ifndef MOTORCONTROLLER_H
#define MOTORCONTROLLER_H

#include <Arduino.h>

class MotorController {
  
private:
    int RPWM;
    int LPWM; 
    int vel; 

public:
    // Construtor
    MotorController(int RPWM,int LPWM);

    // Métodos
    void begin(); 
    void turnBack(int vel); 
    void turnFront(int vel);
    void stop();
};

#endif 
