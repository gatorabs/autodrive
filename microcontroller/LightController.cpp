#include "LightController.h"

#define PIN 40
#define NUMPIXELS 24

Adafruit_NeoPixel pixels = Adafruit_NeoPixel(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

void LightController::setup(){
  pixels.begin();
  for(int i = 0; i <= NUMPIXELS; i++){
    pixels.setPixelColor(i, pixels.Color(0, 255, 255));
    pixels.show();
 }
}