#include "CanController.h"

bool CanController::setup(int pin_1, int pin_2) {
  CAN.setPins(pin_1, pin_2);
  bool canStatus = CAN.begin(500E3);
  return canStatus;
}

void CanController::sendCanMessage(char message) {
  CAN.beginPacket(0x20);
  CAN.write(message);
  CAN.endPacket();
}

char CanController::readCanMessage() {
  int packetSize = CAN.parsePacket();

  if (packetSize > 0 && !CAN.packetRtr()) {
    if (CAN.available()) {
      return (char)CAN.read();  
    }
  }
  return 'N'; 
}
