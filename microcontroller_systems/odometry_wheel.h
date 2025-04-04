#ifndef ODOMETRY_WHEEL_H
#define ODOMETRY_WHEEL_H

#include <Arduino.h>

extern const int pulsesPerRevolution;
extern const float wheelRadiusCm;

extern volatile long encoder1Ticks;
extern volatile long encoder2Ticks;

extern long previousEncoder1Ticks;
extern long previousEncoder2Ticks;

void setup_encoder();
void loop_encoder();

#endif
