import time
import website_manager as wm
import display_manager as dm
import combine_btn_motion as bm
from smarthouse_power_monitor import SmartHousePowerMonitor
import dht
from machine import Pin, PWM
import machine

# Initialize DHT sensor for temperature readings
dht_sensor = dht.DHT11(Pin(17))

# Initialize PowerGoblin integration (update with your PowerGoblin server address)
power_monitor = SmartHousePowerMonitor(goblin_host="10.0.0.201:8080")

# Initialize Fan Control Pins
INA = PWM(Pin(27, Pin.OUT), 10000)  # INA corresponds to IN+
INB = PWM(Pin(18, Pin.OUT), 10000)  # INB corresponds to IN-

# Initialize Button for door control
door_button = Pin(26, Pin.IN, Pin.PULL_UP)  # Button for opening/closing the door

# Initialize PWM for Servo (Door control)
door_servo = PWM(Pin(5))  
door_servo.freq(50)

# Global variables to track state
door_open = False
fan_active = False

def read_temperature():
    """Read temperature from DHT sensor"""
    try:
        dht_sensor.measure()
        inside_temp = dht_sensor.temperature()
        outside_temp = 22  # Placeholder - would come from external sensor
        return inside_temp, outside_temp
    except:
        print("Error reading temperature")
        return 20, 22  # Default values if read fails

def toggle_door_state():
    """Toggle the door state and update power monitoring"""
    global door_open
    door_open = not door_open
    
    # Physically control the door
    control_door(door_open)
    
    # Update fan state based on door state (fan off when door open)
    update_fan_state(not door_open)
    
    # Log door state change for power monitoring
    power_monitor.log_door_state_change(door_open)
    
    return door_open

def control_door(open_door):
    """Control the physical door servo"""
    if open_door:
        door_servo.duty(77)  # Door open (90 degrees)
        print("Door opened.")
    else:
        door_servo.duty(25)  # Door closed (0 degrees)
        print("Door closed.")

def update_fan_state(active):
    """Update the fan state and log power changes"""
    global fan_active
    fan_active = active
    
    # Physically control the fan
    if active:
        activate_fan()
    else:
        deactivate_fan()
    
    # Log fan state change for power monitoring
    power_monitor.log_fan_state_change(fan_active)
    
    return fan_active

def activate_fan():
    """Turn on the fan"""
    INA.duty(0)    # Fan control forward direction
    INB.duty(700)  # Set duty cycle to rotate the fan
    print("Fan activated")

def deactivate_fan():
    """Turn off the fan"""
    INA.duty(0)   # Stop fan
    INB.duty(0)   # Stop fan
    print("Fan deactivated")

def trigger_alert(alert_message):
    """Trigger system alert and log power consumption change"""
    # Update website
    wm.alert_website(alert_message)
    
    # Update display
    dm.force_message(alert_message)
    
    # Log power event
    power_monitor.log_alert_event(alert_message)
    
    # Activate emergency signals
    bm.activate_brake_and_warning()

def check_button_press():
    """Check if door button is pressed and handle the press"""
    if door_button.value() == 0:  # Button pressed (active low)
        time.sleep(0.01)  # Delay to debounce the button
        while door_button.value() == 0:
            pass  # Wait for button release
        toggle_door_state()  # Toggle door state
        return True
    return False

def main():
    print("Starting smart house system with power monitoring")
    
    # Start power measurement
    power_monitor.start_power_measurement()
    power_monitor.start_power_run("Normal operation")
    
    # Initialize display
    dm.write_message("System active")
    
    # Main control variables
    alert_state = False
    alert_length = 0
    rolling_timer = time.time()
    alert_timer = time.time()
    temp_log_timer = time.time()
    
    # Initialize door to closed state
    control_door(door_open)
    
    # Initialize fan based on door state (on if door closed)
    update_fan_state(not door_open)
    
    print("Starting main control loop")
    
    try:
        while True:
            current_time = time.time()
            
            # Check for door button press
            button_pressed = check_button_press()
            
            # Check and log temperature every 60 seconds
            if current_time - temp_log_timer > 60:
                temp_log_timer = current_time
                inside_temp, outside_temp = read_temperature()
                power_monitor.log_temperature(inside_temp, outside_temp)
                
                # Update temperature display
                dm.write_message(f"Out temp: {outside_temp}C\nIn temp: {inside_temp}C")
            
            # Normal operation (no alert)
            if not alert_state:
                # Update rolling message display periodically
                if current_time - rolling_timer > 5:
                    rolling_timer = current_time
                    dm.rolling_message()
                
                # Check for danger conditions
                alert_state, alert_length = bm.detect_alert_state()
                
                # If motion detected, log it for power monitoring
                if alert_state and alert_length > 0:
                    power_monitor.log_motion_detected()
                    alert_timer = current_time
                    
                    # If serious alert, start a new power run to measure emergency response
                    if alert_length >= 5:
                        power_monitor.stop_power_run()
                        power_monitor.start_power_run("Emergency response")
            
            # Alert handling
            else:
                if current_time - alert_timer < alert_length:
                    # Emergency is active
                    dm.force_message("Emergency stop!")
                    bm.activate_brake_and_warning()
                    
                    # Brief pause between warning signals
                    time.sleep(0.5)
                    
                    # Clear signals
                    bm.clear_brake_light()
                    bm.stop_buzzer()
                else:
                    # Alert is over, return to normal operation
                    alert_state = False
                    
                    # Return to normal power run if we were in emergency
                    power_monitor.stop_power_run()
                    power_monitor.start_power_run("Normal operation")
            
            # Small delay to prevent CPU overuse
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        # Clean shutdown on keyboard interrupt
        print("Shutting down smart house system")
        power_monitor.stop_power_measurement()
        
        # Ensure fan is off and door is closed
        deactivate_fan()
        control_door(False)
    
    except Exception as e:
        # Log any errors and attempt to stop power measurement
        print(f"Error in main loop: {e}")
        power_monitor.stop_power_measurement()
        
        # Attempt to safely shutdown hardware
        try:
            deactivate_fan() 
            control_door(False)
        except:
            pass
        
        raise

if __name__ == "__main__":
    main()