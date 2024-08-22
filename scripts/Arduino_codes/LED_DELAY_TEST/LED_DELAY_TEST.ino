int ledPin = 10; // Pin for output pulse

void setup() {
  Serial.begin(115200);
  pinMode(ledPin, OUTPUT); // Set pin 10 as an output
  Serial.println("Arduino ready");
}

void loop() {
  if (Serial.available() > 0) {
    char eventType = Serial.read(); // Read the event type identifier
    Serial.println("Event received: ");
    Serial.println(eventType);

    // Blink the LED
    digitalWrite(ledPin, HIGH);  
    delay(10);  // 10 ms pulse duration
    digitalWrite(ledPin, LOW);   

    // Send a response back to Python
    Serial.print("Blink done for event: ");
    Serial.println(eventType);
  }
}
