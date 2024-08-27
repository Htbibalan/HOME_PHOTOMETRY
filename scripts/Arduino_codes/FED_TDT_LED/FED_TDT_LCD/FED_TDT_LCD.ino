#include <LiquidCrystal.h>

// Initialize the library with the new pin numbers
LiquidCrystal lcd(2, 3, 4, 5, 6, A0);

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

// Initialize the LCD
lcd.begin(16, 2);

// Convert the message to a String object
String message = "...McCutcheonLab Technologies...";

// Scroll the welcome message
for (int i = 0; i < message.length() - 15; i++) {  // message.length() - 15 ensures we stop scrolling when there's no more to display
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(message.substring(i, i + 16));  // Display a substring of the message
  delay(300);  // Adjust delay as needed for smoother scrolling
}

// Clear the display after scrolling completes
lcd.clear();
delay(500);  // Pause briefly before showing the next message

// Display the second message
lcd.setCursor(0, 0); // Move to the first line
lcd.print("System Ready!");
delay(3000); // Show the message for 3 seconds
lcd.clear();

}

void loop() {
  if (Serial.available() > 0) {
    char eventType = Serial.read(); // Read the event type identifier
    Serial.print("Received event type: ");
    Serial.println(eventType); // Print the received event type for debugging

    lcd.clear(); // Clear the previous message
    lcd.print("Event: "); // Start with "Event: "

    switch (eventType) {
      case 'L': // Left poke event
        digitalWrite(leftPokePin, HIGH);
        delay(10);
        digitalWrite(leftPokePin, LOW);
        Serial.println("Left poke LED triggered");
        lcd.setCursor(0, 1); // Move to the second line
        lcd.print("Left Poke");
        break;

      case 'W': // Left with pellet event
        digitalWrite(leftWithPelletPin, HIGH);
        delay(10);
        digitalWrite(leftWithPelletPin, LOW);
        Serial.println("Left with pellet LED triggered");
        lcd.setCursor(0, 1);
        lcd.print("Left + Pellet");
        break;

      case 'R': // Right poke event
        digitalWrite(rightPokePin, HIGH);
        delay(10);
        digitalWrite(rightPokePin, LOW);
        Serial.println("Right poke LED triggered");
        lcd.setCursor(0, 1);
        lcd.print("Right Poke");
        break;

      case 'Q': // Right with pellet event
        digitalWrite(rightWithPelletPin, HIGH);
        delay(10);
        digitalWrite(rightWithPelletPin, LOW);
        Serial.println("Right with pellet LED triggered");
        lcd.setCursor(0, 1);
        lcd.print("Right + Pellet");
        break;

      case 'P': // Pellet in well or pellet intake event
        if (pelletInWell) {
          // Pellet is taken
          digitalWrite(pelletPin, LOW);   // Turn off the signal briefly
          delay(10);                      // Short delay
          pelletInWell = false;           // Update state
          Serial.println("Pellet taken: Signal turned OFF briefly");
          lcd.setCursor(0, 1);
          lcd.print("Pellet Taken");
        } else {
          // Pellet is in the well
          digitalWrite(pelletPin, HIGH);  // Keep the signal on
          pelletInWell = true;            // Update state
          Serial.println("Pellet in well: Signal turned ON");
          lcd.setCursor(0, 1);
          lcd.print("Pellet in Well");
        }
        break;

      default:
        Serial.println("Unknown event type received");
        lcd.setCursor(0, 1);
        lcd.print("Unknown Event");
        break;
    }
  }
}
