import time
import website_manager as wm
import display_manager as dm
import combine_btn_motion as bm
from smarthouse_power_monitor import SmartHousePowerMonitor
import dht
from machine import Pin

# Initialize DHT sensor for temperature readings
dht_sensor = dht.DHT11(Pin(17))

# Initialize PowerGoblin integration (update with your PowerGoblin server address)
power_monitor = SmartHousePowerMonitor(goblin_host="10.0.0.201:8080")

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
    
    # Update fan state based on door state
    update_fan_state(not door_open)
    
    # Log door state change for power monitoring
    power_monitor.log_door_state_change(door_open)
    
    return door_open

def update_fan_state(active):
    """Update the fan state and log power changes"""
    global fan_active
    fan_active = active
    
    # Log fan state change for power monitoring
    power_monitor.log_fan_state_change(fan_active)
    
    return fan_active

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
    
    print("Starting main control loop")
    
    try:
        while True:
            current_time = time.time()
            
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
    
    except Exception as e:
        # Log any errors and attempt to stop power measurement
        print(f"Error in main loop: {e}")
        power_monitor.stop_power_measurement()
        raise

if __name__ == "__main__":
    main()
