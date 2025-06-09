#include "BuzzerController.h"
#include <Arduino.h>

#define LED1 29
#define LED2 27
#define LED3 25
#define BUZZER 31

#define NOTE_C5 523
#define NOTE_E5 659
#define NOTE_G5 784
#define NOTE_C6 1047

#define HIGH_BEEP 1000

void BuzzerController::setup() {
  pinMode(BUZZER, OUTPUT);
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);

  beep(LED1);
  beep(LED2);
  beep(LED3);

  soundConclusion();  
}

void BuzzerController::soundConclusion() {
  tone(BUZZER, NOTE_C5, 150);
  delay(200);
  tone(BUZZER, NOTE_E5, 150);
  delay(200);
  tone(BUZZER, NOTE_G5, 150);
  delay(200);
  tone(BUZZER, NOTE_C6, 300);
  delay(300);
  noTone(BUZZER);
}

void BuzzerController::beep(int led) {
  for (int i = 0; i < 3; i++) {
    digitalWrite(led, HIGH);
    tone(BUZZER, HIGH_BEEP);
    delay(300);
    digitalWrite(led, LOW);
    noTone(BUZZER);
    delay(300);
  }
  digitalWrite(led, HIGH);
}
