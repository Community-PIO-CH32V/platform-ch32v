#include <Arduino.h>
#include <Adafruit_TinyUSB.h> // technically not needed, but we can include it anyway

/* PA1 as blinky LED, change here as needed */
#define LED PA1
void setup() {
  Serial.begin(115200); // Serial is a SerialTinyUSB object! :)
  pinMode(LED, OUTPUT);
}

void loop() {
  digitalWrite(LED, HIGH);
  delay(1000);
  digitalWrite(LED, LOW);
  delay(1000);
}