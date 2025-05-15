from machine import Pin, PWM
import machine
import time
import dht

# Initialize Fan Control Pins
INA = PWM(Pin(27, Pin.OUT), 10000)  # INA corresponds to IN+
INB = PWM(Pin(18, Pin.OUT), 10000)  # INB corresponds to IN-

# Initialize Button for door control
button1 = Pin(26, Pin.IN, Pin.PULL_UP)  # Button for opening/closing the door

# Initialize PWM for Servo (Door control)
pwm = PWM(Pin(5))  
pwm.freq(50)

#Associate DHT11 with Pin(17).
DHT = dht.DHT11(machine.Pin(17))


# RGB colors (Red for brake light, for indication when door is open)


# Fan control functions
def activate_fan():
    INA.duty(0)   # Fan control forward direction
    INB.duty(700) # Set duty cycle to rotate the fan

def deactivate_fan():
    INA.duty(0)   # Stop fan
    INB.duty(0)   # Stop fan

# Function to simulate door control with PWM (servo motor)
def control_door(open_door):
    if open_door:
        pwm.duty(77)  # Door open (90 degrees)
        print("Door opened.")
    else:
        pwm.duty(25)  # Door closed (0 degrees)
        print("Door closed.")

# Main loop to toggle door and control fan
door_open = False  # Initially, door is closed

while True:
    btnVal1 = button1.value()  # Read the button value (active low)
    DHT.measure()
    
    if btnVal1 == 0:  # Button pressed (active low)
        time.sleep(0.01)  # Delay to debounce the button
        while btnVal1 == 0:
            btnVal1 = button1.value()  # Wait for button release
        door_open = not door_open  # Toggle door state
        
        # Control the door based on the state
        control_door(door_open)
        
        # Control the fan based on door state
        if door_open:
            deactivate_fan()  # Turn off fan if door is open
        else:
            activate_fan()  # Turn on fan if door is closed

    time.sleep(0.1)  # Short delay to prevent rapid toggling
