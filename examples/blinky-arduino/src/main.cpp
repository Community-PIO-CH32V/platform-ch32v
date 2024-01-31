#include <Arduino.h>

/* PC3 as blinky LED, change here as needed */
#define LED PC3
void setup() {
  pinMode(LED, OUTPUT);
}

void loop() {
  digitalWrite(LED, HIGH);
  delay(1000);
  digitalWrite(LED, LOW);
  delay(1000);
}