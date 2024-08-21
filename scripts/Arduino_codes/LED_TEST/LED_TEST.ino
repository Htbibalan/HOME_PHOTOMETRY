int ledPin = 10; // Use pin 10 for the LED

void setup() {
  pinMode(ledPin, OUTPUT); // Set pin 10 as an output
}

void loop() {
  digitalWrite(ledPin, HIGH); // Turn the LED on
  delay(1000);                // Wait for 1 second
  digitalWrite(ledPin, LOW);  // Turn the LED off
  delay(1000);                // Wait for 1 second
}
