#include <Arduino.h>

// Can also define a blinky LED here for easy checking if the board is running!
//#define LED PA5
// Depending on build flags, Serial should either be regular UART or USB CDC!
void setup() {
  Serial.begin(115200);
#ifdef LED
  pinMode(LED, OUTPUT);
#endif
}

void loop() {
#ifdef LED
  digitalWrite(LED, digitalRead(LED) ^ 1);
#endif
  Serial.println("Hello, world!");
  delay(1000);
}