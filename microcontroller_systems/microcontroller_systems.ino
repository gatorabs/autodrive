#include "serial_processor.h"
#include "servo_control.h"
#include "motor_control.h"

unsigned long lastSerialReadTime = 0;
unsigned long serialInterval = 10;  // a cada 10 ms

unsigned long lastControlUpdateTime = 0;
unsigned long controlInterval = 15;  // a cada 15 ms

void setup() {
    setupSerialProcessor();
    setupServo();
}

void loop() {
    unsigned long currentTime = millis();


    if (currentTime - lastSerialReadTime >= serialInterval) {
        lastSerialReadTime = currentTime;
        updateSerialInput();
    }

    if (currentTime - lastControlUpdateTime >= controlInterval) {
        lastControlUpdateTime = currentTime;

        setServoAngle(angulacao);

        if (velocidade > 0) {
            motor_control(HIGH, LOW, HIGH, LOW, velocidade, velocidade);
            digitalWrite(LED_PIN, LOW);
        } else if (velocidade < 0) {
            motor_control(LOW, HIGH, LOW, HIGH, abs(velocidade), abs(velocidade));
        } else {
            motor_control(LOW, LOW, LOW, LOW, 0, 0);
            digitalWrite(LED_PIN, HIGH);
        }
    }
}

