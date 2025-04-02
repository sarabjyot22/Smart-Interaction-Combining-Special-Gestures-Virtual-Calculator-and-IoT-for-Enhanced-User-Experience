// Define pins for LEDs
const int ledPins[] = {3, 5, 6, 9, 11};  // Array to hold LED pin numbers

void setup() {
  // Set all LED pins as OUTPUT
  for (int i = 0; i < 5; i++) {
    pinMode(ledPins[i], OUTPUT);
  }
}

void loop() {
  // Turn all LEDs on
  for (int i = 0; i < 5; i++) {
    digitalWrite(ledPins[i], HIGH);
    delay(500);  // Wait 500ms
  }

  
}
