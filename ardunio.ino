// Pin assignments for LEDs
int green = 11;  // PWM pin
int white = 5;   // PWM pin
int blue = 6;    // PWM pin
int yellow = 9;  // PWM pin
int red = 10;    // PWM pin

void setup() {
  Serial.begin(115200);
  pinMode(green, OUTPUT);
  pinMode(white, OUTPUT);
  pinMode(blue, OUTPUT);
  pinMode(yellow, OUTPUT);
  pinMode(red, OUTPUT);
  turnOffAllLights();
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    if (input.length() > 1) {
      char mode = input[0];
      int fingerCount = input.substring(1).toInt();

      if (mode == 'I') {
        controlIntensity(fingerCount);
      } else if (mode == 'L') {
        controlSingleLight(fingerCount);
      }
    }
  }
}

void controlIntensity(int count) {
  int brightness = map(count, 0, 5, 0, 255);
  analogWrite(green, brightness);
  analogWrite(white, brightness);
  analogWrite(blue, brightness);
  analogWrite(yellow, brightness);
  analogWrite(red, brightness);
}

void controlSingleLight(int count) {
  turnOffAllLights();
  if (count == 1) digitalWrite(green, HIGH);
  if (count == 2) digitalWrite(white, HIGH);
  if (count == 3) digitalWrite(blue, HIGH);
  if (count == 4) digitalWrite(yellow, HIGH);
  if (count == 5) digitalWrite(red, HIGH);
}

void turnOffAllLights() {
  digitalWrite(green, LOW);
  digitalWrite(white, LOW);
  digitalWrite(blue, LOW);
  digitalWrite(yellow, LOW);
  digitalWrite(red, LOW);
}
