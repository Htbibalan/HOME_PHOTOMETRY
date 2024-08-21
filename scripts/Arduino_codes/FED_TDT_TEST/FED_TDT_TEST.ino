//int pulsePin = 10; // Use pin 10 for the LED or pulse output
//
//void setup() {
//  Serial.begin(115200);
//  pinMode(pulsePin, OUTPUT); // Set pin 10 as an output
//}
//
//void loop() {
//  if (Serial.available() > 0) {
//    String data = Serial.readStringUntil('\n');
//    
//    // Generate a pulse when data is received
//    digitalWrite(pulsePin, HIGH);  // Turn the LED on or send a pulse
//    delay(10);                     // 10 ms pulse duration
//    digitalWrite(pulsePin, LOW);   // Turn the LED off or end the pulse
//    
//    Serial.print("Received: ");
//    Serial.println(data);  // Print the received data to the Serial Monitor
//  }
//}



int pulsePin = 10; // Digital pin for output pulse to TDT

void setup() {
  Serial.begin(115200); // Initialize serial communication at 115200 baud rate
  pinMode(pulsePin, OUTPUT); // Set pin 10 as an output for the pulse
}

void loop() {
  if (Serial.available() > 0) { 
    // Check if data is available to read from the serial port
    char incomingByte = Serial.read(); // Read the incoming byte
    
    // Generate a pulse on pin 10 to send a signal to the TDT system
    digitalWrite(pulsePin, HIGH);  // Send a HIGH signal (pulse) to TDT
    delay(10);                     // 10 ms pulse duration (adjust if needed)
    digitalWrite(pulsePin, LOW);   // End the pulse (set pin 10 to LOW)

    // (Optional) Print the received byte for debugging
    Serial.print("Received: ");
    Serial.println(incomingByte);
  }
}
