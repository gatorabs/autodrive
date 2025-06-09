#ifndef CANCONTROLLER_H
#define CANCONTROLLER_H

#include <Arduino.h>
#include <CAN.h>

class CanController {
  public:
    void setup(int pin_1, int pin_2);
    void sendCanMessage(char message);
    char readCanMessage();
};

#endif