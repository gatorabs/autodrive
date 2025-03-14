#include "serial_processor.h"
#include "servo_control.h"  

void setup() {
    setupSerialProcessor();
    setupServo();
}

void loop() {
    updateSerialInput();
}
