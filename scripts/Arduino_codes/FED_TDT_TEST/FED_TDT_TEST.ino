//////////////// Here I am just testing the output using LED
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

/////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////

//same code just different documentation 

//int pulsePin = 10; // Digital pin for output pulse to TDT
//
//void setup() {
//  Serial.begin(115200); // Initialize serial communication at 115200 baud rate
//  pinMode(pulsePin, OUTPUT); // Set pin 10 as an output for the pulse
//}
//
//void loop() {
//  if (Serial.available() > 0) { 
//    // Check if data is available to read from the serial port
//    char incomingByte = Serial.read(); // Read the incoming byte
//    
//    // Generate a pulse on pin 10 to send a signal to the TDT system
//    digitalWrite(pulsePin, HIGH);  // Send a HIGH signal (pulse) to TDT
//    delay(10);                     // 10 ms pulse duration (adjust if needed)
//    digitalWrite(pulsePin, LOW);   // End the pulse (set pin 10 to LOW)
//
//    // (Optional) Print the received byte for debugging
//    Serial.print("Received: ");
//    Serial.println(incomingByte);
//  }
//}


///////////////////////////////
//we can try this code to send distinct TTLs to TDT
//int pulsePin = 10; // Pin for output pulse
//
//void setup() {
//  Serial.begin(115200);
//  pinMode(pulsePin, OUTPUT); // Set pin 10 as an output
//}
//
//void loop() {
//  if (Serial.available() > 0) {
//    char eventType = Serial.read(); // Read the event type identifier
//
//    switch(eventType) {
//      case 'R': // Right poke event
//        generatePulse(1); // Single pulse
//        break;
//      case 'L': // Left poke event
//        generatePulse(2); // Double pulse
//        break;
//      case 'P': // Pellet intake event
//        generatePulse(3); // Triple pulse
//        break;
//      case 'W': // Left with pellet event
//        generatePulse(4); // Quadruple pulse
//        break;
//      case 'Q': // Right with pellet event
//        generatePulse(5); // Quintuple pulse
//        break;
//    }
//  }
//}
//
//void generatePulse(int pulseCount) {
//  for (int i = 0; i < pulseCount; i++) {
//    digitalWrite(pulsePin, HIGH);  // Send a pulse
//    delay(10);                     // 10 ms pulse duration
//    digitalWrite(pulsePin, LOW);   // End the pulse
//    delay(100);                    // Wait 100 ms between pulses
//  }
//}
//

///////////////////////////
//here trying to send different TTL signals through separate pins for each behavioural event
//int leftPokePin = 9;           // Pin for left poke event
//int leftWithPelletPin = 10;    // Pin for left poke with pellet event
//int rightPokePin = 11;         // Pin for right poke event
//int rightWithPelletPin = 12;   // Pin for right poke with pellet event
//int pelletIntakePin = 13;      // Pin for pellet intake event
//
//void setup() {
//  Serial.begin(115200);
//  pinMode(leftPokePin, OUTPUT);         // Set pin 9 as an output
//  pinMode(leftWithPelletPin, OUTPUT);   // Set pin 10 as an output
//  pinMode(rightPokePin, OUTPUT);        // Set pin 11 as an output
//  pinMode(rightWithPelletPin, OUTPUT);  // Set pin 12 as an output
//  pinMode(pelletIntakePin, OUTPUT);     // Set pin 13 as an output
//}
//void loop() {
//  if (Serial.available() > 0) {
//    char eventType = Serial.read(); // Read the event type identifier
//    Serial.print("Received event type: ");
//    Serial.println(eventType); // Print the received event type for debugging
//
//    switch(eventType) {
//      case 'l': // Left poke event
//        Serial.println("Triggering left poke pin (9)");
//        generatePulse(leftPokePin);   // Send pulse on left poke pin
//        break;
//      case 'w': // Left with pellet event
//        Serial.println("Triggering left with pellet pin (10)");
//        generatePulse(leftWithPelletPin); // Send pulse on left with pellet pin
//        break;
//      case 'r': // Right poke event
//        Serial.println("Triggering right poke pin (11)");
//        generatePulse(rightPokePin);  // Send pulse on right poke pin
//        break;
//      case 'q': // Right with pellet event
//        Serial.println("Triggering right with pellet pin (12)");
//        generatePulse(rightWithPelletPin); // Send pulse on right with pellet pin
//        break;
//      case 'p': // Pellet intake event
//        Serial.println("Triggering pellet intake pin (13)");
//        generatePulse(pelletIntakePin);  // Send pulse on pellet intake pin
//        break;
//      default:
//        Serial.println("Unknown event type received.");
//        break;
//    }
//  }
//}
//
//
//void generatePulse(int pin) {
//  digitalWrite(pin, HIGH);  // Send a pulse
//  delay(10);                // 10 ms pulse duration
//  digitalWrite(pin, LOW);   // End the pulse
//}
//
//

/////
///Testing LED functions and making sure Python interacts correctly
//int leftPokePin = 9;           // Pin for left poke event
//int rightPokePin = 11;         // Pin for right poke event
//int pelletIntakePin = 13;      // Pin for pellet intake event
//
//void setup() {
//  Serial.begin(115200);
//  pinMode(leftPokePin, OUTPUT);         
//  pinMode(rightPokePin, OUTPUT);        
//  pinMode(pelletIntakePin, OUTPUT);     
//}
//
//void loop() {
//  if (Serial.available() > 0) {
//    char eventType = Serial.read(); // Read the event type identifier
//    Serial.print("Received event type: ");
//    Serial.println(eventType); // Print the received event type for debugging
//
//    if (eventType == 'L') {
//        digitalWrite(leftPokePin, HIGH);   // Turn on left poke LED
//        delay(1000);                       // Keep it on for 1 second
//        digitalWrite(leftPokePin, LOW);    // Turn it off
//        Serial.println("Left poke LED triggered");
//    } 
//    else if (eventType == 'R') {
//        digitalWrite(rightPokePin, HIGH);  // Turn on right poke LED
//        delay(1000);                       // Keep it on for 1 second
//        digitalWrite(rightPokePin, LOW);   // Turn it off
//        Serial.println("Right poke LED triggered");
//    } 
//    else if (eventType == 'P') {
//        digitalWrite(pelletIntakePin, HIGH);  // Turn on pellet intake LED
//        delay(1000);                          // Keep it on for 1 second
//        digitalWrite(pelletIntakePin, LOW);   // Turn it off
//        Serial.println("Pellet intake LED triggered");
//    }
//  }
//}

/////////////////////////////////////////////////////Here the latest code////////////////////////////////////

//int leftPokePin = 9;           // Pin for left poke event
//int leftWithPelletPin = 10;    // Pin for left poke with pellet event
//int rightPokePin = 11;         // Pin for right poke event
//int rightWithPelletPin = 12;   // Pin for right poke with pellet event
//int pelletIntakePin = 13;      // Pin for pellet intake event
//
//void setup() {
//  Serial.begin(115200);
//  pinMode(leftPokePin, OUTPUT);         
//  pinMode(leftWithPelletPin, OUTPUT);   
//  pinMode(rightPokePin, OUTPUT);        
//  pinMode(rightWithPelletPin, OUTPUT);  
//  pinMode(pelletIntakePin, OUTPUT);     
//}
//
//void loop() {
//  if (Serial.available() > 0) {
//    char eventType = Serial.read(); // Read the event type identifier
//    Serial.print("Received event type: ");
//    Serial.println(eventType); // Print the received event type for debugging
//
//    if (eventType == 'L') {
//        digitalWrite(leftPokePin, HIGH);   // Turn on left poke LED
//        delay(1000);                       // Keep it on for 1 second
//        digitalWrite(leftPokePin, LOW);    // Turn it off
//        Serial.println("Left poke LED triggered");
//    } 
//    else if (eventType == 'W') {
//        digitalWrite(leftWithPelletPin, HIGH);  // Turn on left with pellet LED
//        delay(1000);                            // Keep it on for 1 second
//        digitalWrite(leftWithPelletPin, LOW);   // Turn it off
//        Serial.println("Left with pellet LED triggered");
//    } 
//    else if (eventType == 'R') {
//        digitalWrite(rightPokePin, HIGH);  // Turn on right poke LED
//        delay(1000);                       // Keep it on for 1 second
//        digitalWrite(rightPokePin, LOW);   // Turn it off
//        Serial.println("Right poke LED triggered");
//    } 
//    else if (eventType == 'Q') {
//        digitalWrite(rightWithPelletPin, HIGH);  // Turn on right with pellet LED
//        delay(1000);                             // Keep it on for 1 second
//        digitalWrite(rightWithPelletPin, LOW);   // Turn it off
//        Serial.println("Right with pellet LED triggered");
//    }
//    else if (eventType == 'P') {
//        digitalWrite(pelletIntakePin, HIGH);  // Turn on pellet intake LED
//        delay(1000);                          // Keep it on for 1 second
//        digitalWrite(pelletIntakePin, LOW);   // Turn it off
//        Serial.println("Pellet intake LED triggered");
//    }
//  }
//}



/////////////////////////Pellet_in_well_signal////////////////////
int leftPokePin = 9;           // Pin for left poke event
int leftWithPelletPin = 10;    // Pin for left poke with pellet event
int rightPokePin = 11;         // Pin for right poke event
int rightWithPelletPin = 12;   // Pin for right poke with pellet event
int pelletPin = 13;            // Pin for both pellet in well and pellet intake events

bool pelletInWell = false;  // State variable to track if pellet is in the well

void setup() {
  Serial.begin(115200);

  // Setup pins as outputs
  pinMode(leftPokePin, OUTPUT);         
  pinMode(leftWithPelletPin, OUTPUT);   
  pinMode(rightPokePin, OUTPUT);        
  pinMode(rightWithPelletPin, OUTPUT);  
  pinMode(pelletPin, OUTPUT);     

  // Ensure all pins start LOW
  digitalWrite(leftPokePin, LOW);
  digitalWrite(leftWithPelletPin, LOW);
  digitalWrite(rightPokePin, LOW);
  digitalWrite(rightWithPelletPin, LOW);
  digitalWrite(pelletPin, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    char eventType = Serial.read(); // Read the event type identifier
    Serial.print("Received event type: ");
    Serial.println(eventType); // Print the received event type for debugging

    switch (eventType) {
      case 'L': // Left poke event
        digitalWrite(leftPokePin, HIGH);
        delay(10);
        digitalWrite(leftPokePin, LOW);
        Serial.println("Left poke LED triggered");
        break;

      case 'W': // Left with pellet event
        digitalWrite(leftWithPelletPin, HIGH);
        delay(10);
        digitalWrite(leftWithPelletPin, LOW);
        Serial.println("Left with pellet LED triggered");
        break;

      case 'R': // Right poke event
        digitalWrite(rightPokePin, HIGH);
        delay(10);
        digitalWrite(rightPokePin, LOW);
        Serial.println("Right poke LED triggered");
        break;

      case 'Q': // Right with pellet event
        digitalWrite(rightWithPelletPin, HIGH);
        delay(10);
        digitalWrite(rightWithPelletPin, LOW);
        Serial.println("Right with pellet LED triggered");
        break;

      case 'P': // Pellet in well or pellet intake event
        if (pelletInWell) {
          // Pellet is taken
          digitalWrite(pelletPin, LOW);   // Turn off the signal briefly
          delay(10);                      // Short delay
          pelletInWell = false;           // Update state
          Serial.println("Pellet taken: Signal turned OFF briefly");
        } else {
          // Pellet is in the well
          digitalWrite(pelletPin, HIGH);  // Keep the signal on
          pelletInWell = true;            // Update state
          Serial.println("Pellet in well: Signal turned ON");
        }
        break;

      default:
        Serial.println("Unknown event type received");
        break;
    }
  }
}
