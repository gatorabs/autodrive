#include <ESP32Servo.h>

#define RPM_A 32
#define RPM_B 14

#define IN1 33
#define IN2 25
#define IN3 27
#define IN4 26

#define LED_PIN 2
#define SERVO_PIN 18

Servo myServo;

String inputString = "";
bool packetComplete = false;

int direction = 0;
int speedValue = 0;
int extraValue = 0;

void setup() {
  Serial.begin(115200);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(RPM_A, OUTPUT);
  pinMode(RPM_B, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  myServo.attach(SERVO_PIN);
  inputString.reserve(50);
}

void loop() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();

    if (inChar == '#') {
      packetComplete = true;
      break;
    } else {
      inputString += inChar;
    }
  }

  if (packetComplete) {
    parseAndExecute(inputString);
    inputString = "";
    packetComplete = false;

    digitalWrite(LED_PIN, HIGH);  // Liga o LED ao receber pacote completo
    delay(100);                   // Pisca rápido para indicar
    digitalWrite(LED_PIN, LOW);
  }
}

void parseAndExecute(String data) {
  int values[3];
  int index = 0;
  char *token = strtok((char*)data.c_str(), ",");

  while (token != NULL && index < 3) {
    values[index++] = atoi(token);
    token = strtok(NULL, ",");
  }

  if (index == 3) {
    direction = values[0];
    speedValue = constrain(values[1], 0, 255);
    extraValue = values[2];

    // Servo Motor
    myServo.write(direction);  // Espera ângulo de 0 a 180

    // Motor DC (exemplo: frente com velocidade igual nos dois motores)
    motor_control(HIGH, LOW, HIGH, LOW, speedValue, speedValue);
  }
}

void motor_control(int m1_a, int m1_b, int m2_a, int m2_b, int speedA, int speedB) {
  if (speedA == 0) {
    // Inverte os sinais de direção para frear (freio motor ativo)
    digitalWrite(IN1, !m1_b);  // Inverso de m1_a
    digitalWrite(IN2, !m1_a);
    digitalWrite(IN3, !m2_a);
    digitalWrite(IN4, !m2_b);

    setMotorSpeed(255, 255);
    setMotorSpeed(0, 0);
  } else {
    // Controle normal
    digitalWrite(IN1, m1_b);
    digitalWrite(IN2, m1_a);
    digitalWrite(IN3, m2_a);
    digitalWrite(IN4, m2_b);

    setMotorSpeed(speedA, speedB);
  }
}


void setMotorSpeed(int motorA_speed, int motorB_speed) {
  analogWrite(RPM_A, motorA_speed);
  analogWrite(RPM_B, motorB_speed);
}
