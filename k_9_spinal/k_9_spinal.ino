#include <CmdMessenger.h>
#include <Servo.h>


Servo myservo[3];

char field_separator = ' ';
char command_separator = ';';
CmdMessenger cmdMessenger = CmdMessenger(Serial, field_separator);
//CmdMessenger (Stream& Serial, const char field_separator, const char command_separator, const char escape_character);
enum
{
  kCommandList         , 
  kStatus              , 
  kSetD                ,
  kSetPWM              ,
  kSetServo            ,
  kSetServoMS            ,
  kGetA                , 
  kGetD                ,
  kSetTracks
};

int angle;
unsigned long laststatstime;

void attachCommandCallbacks()
{
  // Attach callback methods
  cmdMessenger.attach(OnUnknownCommand);
  cmdMessenger.attach(kCommandList, OnCommandList);
  cmdMessenger.attach(kStatus, OnStatus);
  cmdMessenger.attach(kSetD, OnSetD);
  cmdMessenger.attach(kSetPWM, OnSetPWM);
  cmdMessenger.attach(kSetServo, OnSetServo);
  cmdMessenger.attach(kSetServoMS, OnSetServoMS);
  cmdMessenger.attach(kGetA, OnGetA);
  cmdMessenger.attach(kGetD, OnGetD);
  cmdMessenger.attach(kSetTracks, OnSetTracks);
  
}




// Called when a received command has no attached function
void OnUnknownCommand()
{
  Serial.println("ERR: UNKNOWN COMMAND");
  ShowCommands();
}

// Callback function that shows a list of commands
void OnCommandList()
{
  ShowCommands();
}

// Callback function that shows led status
void OnStatus()
{
  // Send back status that describes the led state
  ShowStatus();  
}

void ShowStatus() 
{
  Serial.println("==========-------Current status---------===========");
  for (int i=2; i<=12; i++){
      Serial.print("DPIN# ");
      Serial.print(i);
      Serial.print('=');
      Serial.println(digitalRead(i));
  }
  for (int i=1; i<=3; i++){
      Serial.print("APIN# ");
      Serial.print(i);
      Serial.print('=');
      Serial.println(analogRead(i));
  }
  for (int i=1; i<=3; i++){
      Serial.print("Servo# ");
      Serial.print(i);
      Serial.print('=');
      Serial.println(myservo[i].read());
  }
  Serial.print("Big Li-Ion voltage is: ");
  Serial.println (analogRead(3)*0.0097956);
  SendStatus();
}

void OnSetPWM() 
{
  int pin = cmdMessenger.readIntArg();  
  boolean val = cmdMessenger.readIntArg();  
  analogWrite(pin, val);   
  SendStatus();
  Serial.println ("OK PWM " + String(pin) + " " + String(val));
}

void OnGetD() 
{
  int pin = cmdMessenger.readIntArg();  
  int val = digitalRead(pin);
  Serial.println (String(val));  
}

void OnGetA() 
{
  int pin = cmdMessenger.readIntArg();  
  int val = analogRead(pin);
  Serial.println (String(val));  
}

void SendStatus()
{
  int bitnum = 0;
  byte result[11];
  String debug;
  result[0] = '#';
  byte buffer = 0;
  for (int i=2; i<=10; i++){
      if (i == 5 or i == 6) {
        bitWrite(buffer,bitnum,true);
        continue;
      }
      bitWrite(buffer,bitnum,digitalRead(i));
      bitnum++;   
  }
 result[1] = buffer;
 for (int i=1; i<=2; i++){
      result[(i+1)] = myservo[i].read();
  }    
  int j=4;
  for (int i=1; i<=3; i++){
      int adc=analogRead(i);
//      debug += String(analogRead(i)) + ':';    
      result[j] = highByte(adc);
//      debug += String(result[j]) + ' ';
      j++;
      result[j] = lowByte(adc);
//      debug += String(result[j]) + ' ';
      j++;
  }
 result[j] = '#';
 Serial.write (result, 11);
 laststatstime = millis();
// Serial.println (debug);
}


// Show available commands
void ShowCommands() 
{
  Serial.println('Available commands');
  Serial.println(' 0;- This command list');
  Serial.println(' 1;- Show status');
  Serial.println(' 2 <pin> <bool>; - Set digital out');
  Serial.println(' 3 <pin> <byte>; - Set pwm out');
  Serial.println(' 4 <servo> <byte>; - Set servo angle');
  Serial.println(' 5 <servo> <byte>; - Set servo ms');
  Serial.println(' 6 <pin>; - Read analog in');
  Serial.println(' 7 <pin>; - Read digital in');
  Serial.println(' 8 <LFWD> <LREV> <LPWM> <RFWD> <RREV> <RPWM>;            - Set tracks ');
}

void OnSetD()
{
  // Read GPIO state argument, expects 0 or 1 and interprets as false or true 
  int pin = cmdMessenger.readIntArg();  
  boolean level = cmdMessenger.readBoolArg();  
  digitalWrite(pin, level);   
  SendStatus();
  Serial.println ("OK SETD " + String(pin) + " " + String(level));
}

void OnSetTracks()
{
#define p1PWM 6
#define p1FWD 7
#define p1REV 8
#define p2PWM 5
#define p2FWD 4
#define p2REV 3


  boolean lfwd = cmdMessenger.readBoolArg();    
  boolean lrev = cmdMessenger.readBoolArg();      
  int lpwm = cmdMessenger.readIntArg();  
  boolean rfwd = cmdMessenger.readBoolArg();    
  boolean rrev = cmdMessenger.readBoolArg();      
  int rpwm = cmdMessenger.readIntArg();  
  digitalWrite(p2FWD, lfwd);   
  digitalWrite(p2REV, lrev);    
  digitalWrite(p1FWD, rfwd);   
  digitalWrite(p1REV, rrev);    
  analogWrite(p1PWM, rpwm);   
  analogWrite(p2PWM, lpwm);    
    
  SendStatus();
  Serial.println ("OK TRACKS " + String(lfwd) + " " + String(lrev) + " " + String(lpwm) + " "  + String(rfwd) + " " + String(rrev) + " " + String(rpwm));
}



// Callback function that sets led on or off
void OnSetServo()
{
  int servo = cmdMessenger.readIntArg();  
  int angle = cmdMessenger.readIntArg();  
  if (angle > 180 or angle < 0) {
    Serial.println ("Angle " + String(angle) +" wrong, ignoring");    
    return; 
  }
  myservo[servo].write(angle);
  SendStatus();
  Serial.println ("OK SERVO "+ String(servo) + " " + String(angle));
}

void OnSetServoMS()
{
  int servo = cmdMessenger.readIntArg();  
  int ms = cmdMessenger.readIntArg();  
  myservo[servo].writeMicroseconds(ms);
SendStatus();
Serial.println ("OK SERVOMS " + String(servo) + " " + String(ms));
}


void setup()                    
{                             
  pinMode(2, OUTPUT);        
  pinMode(3, OUTPUT);        
  pinMode(4, OUTPUT);        
  pinMode(5, OUTPUT);        
  pinMode(6, OUTPUT);        
  pinMode(7, OUTPUT);        
  pinMode(8, OUTPUT);        
  pinMode(9, OUTPUT);        
  pinMode(10, OUTPUT);        
  pinMode(11, OUTPUT);        
  pinMode(12, OUTPUT);        
  pinMode(13, OUTPUT);        
  analogReference(INTERNAL);
  
  // Listen on serial connection for messages from the PC
  Serial.begin(115200); 
  cmdMessenger.printLfCr();     // Adds newline to every command
  attachCommandCallbacks();   // Attach my application's user-defined callback methods
  Serial.println ("0_o\nK-9 Spinal booted up");
  myservo[1].attach(11,900,2100);
  myservo[2].attach(12);
  myservo[3].attach(10);
//  myservo[3].write(110);
  laststatstime = millis();
  SendStatus();

}                               




void loop()                     
{
  digitalWrite(13, LOW);
  delay (50);
  cmdMessenger.feedinSerialData();
  digitalWrite(13, HIGH);
  delay (50);
  cmdMessenger.feedinSerialData();
  if  (laststatstime + 1000 < millis()) {
       SendStatus();
  }

}                               
