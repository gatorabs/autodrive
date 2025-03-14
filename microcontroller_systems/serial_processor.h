#ifndef SERIAL_PROCESSOR_H
#define SERIAL_PROCESSOR_H

#include <Arduino.h>

#define BUFFER_SIZE 32    // Tamanho máximo do buffer de entrada
#define MAX_VALUES 10     // Número máximo de valores esperados
#define LED_PIN 2        // Pino do LED interno

extern int receivedData[MAX_VALUES];
extern int velocidade;
extern int angulacao;
extern int semaforo;

void setupSerialProcessor();
void processData(char *data);
void updateSerialInput();

#endif  // SERIAL_PROCESSOR_H
