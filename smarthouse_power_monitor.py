from power_goblin_manager import PowerGoblinManager
import time

class SmartHousePowerMonitor:
    """
    Integrates the smart house components with PowerGoblin power measurement
    """
    def __init__(self, goblin_host="10.0.0.201:8080"):
        self.pgm = PowerGoblinManager(host=goblin_host)
        self.pgm.start_session()
        
        # Set up meters
        self.meters = self.pgm.get_meters()
        if self.meters:
            print(f"Available meters: {self.meters}")
            
        # Initialize power tracking
        self.measurement_active = False
        self.run_active = False
        
        # Track events for power correlation
        self.last_alert_time = 0
        self.last_door_state = False
        self.last_fan_state = False
        
        # Rename channels for clarity
        try:
            if self.meters:
                self.pgm.rename_meter_channel("0", "0", "Main_Power")
                self.pgm.rename_meter_channel("0", "1", "Motor_Power")
                self.pgm.rename_meter_channel("0", "2", "LED_Power")
        except:
            print("Could not rename meter channels")
    
    def start_power_measurement(self):
        """Start power measurement session"""
        if not self.measurement_active:
            print("Starting power measurement")
            self.pgm.start_measurement(message="Smart house power monitoring")
            self.measurement_active = True
            return True
        return False
    
    def stop_power_measurement(self):
        """Stop power measurement session"""
        if self.measurement_active:
            print("Stopping power measurement")
            if self.run_active:
                self.pgm.stop_run(message="Run ending with measurement")
                self.run_active = False
            self.pgm.stop_measurement(message="Smart house power monitoring complete")
            self.measurement_active = False
            return True
        return False
    
    def start_power_run(self, label=""):
        """Start a run within the measurement"""
        if self.measurement_active and not self.run_active:
            run_name = f"Smart house run{' - ' + label if label else ''}"
            print(f"Starting power run: {run_name}")
            self.pgm.start_run(message=run_name)
            self.run_active = True
            return True
        return False
    
    def stop_power_run(self):
        """Stop the current run"""
        if self.run_active:
            print("Stopping power run")
            self.pgm.stop_run(message="Smart house run complete")
            self.run_active = False
            return True
        return False
    
    def log_alert_event(self, alert_message):
        """Log a power event when an alert is triggered"""
        current_time = time.time()
        
        # Prevent duplicate triggers in short timespan
        if current_time - self.last_alert_time < 2:
            return False
            
        print(f"Logging alert power event: {alert_message}")
        self.last_alert_time = current_time
        
        # Make sure measurement is active
        if not self.measurement_active:
            self.start_power_measurement()
            
        # Create a trigger for this alert
        self.pgm.create_trigger("Alert", alert_message)
        
        # Add custom resource data
        self.pgm.add_custom_resource("alert_count", "1")
        
        return True
    
    def log_door_state_change(self, door_open):
        """Log power consumption changes when door state changes"""
        if door_open != self.last_door_state:
            self.last_door_state = door_open
            
            door_state = "opened" if door_open else "closed"
            print(f"Logging door state change: {door_state}")
            
            # Make sure measurement is active
            if not self.measurement_active:
                self.start_power_measurement()
                
            # Create a trigger for this door state change
            self.pgm.create_trigger("DoorState", f"Door {door_state}")
            
            return True
        return False
    
    def log_fan_state_change(self, fan_active):
        """Log power consumption changes when fan state changes"""
        if fan_active != self.last_fan_state:
            self.last_fan_state = fan_active
            
            fan_state = "activated" if fan_active else "deactivated"
            print(f"Logging fan state change: {fan_state}")
            
            # Make sure measurement is active
            if not self.measurement_active:
                self.start_power_measurement()
                
            # Create a trigger for this fan state change
            self.pgm.create_trigger("FanState", f"Fan {fan_state}")
            
            return True
        return False
    
    def log_temperature(self, inside_temp, outside_temp):
        """Log temperature readings as resource data"""
        if self.measurement_active:
            print(f"Logging temperature data: Inside {inside_temp}C, Outside {outside_temp}C")
            
            # Add temperature data as custom resources
            self.pgm.add_custom_resource("temperature_inside", str(inside_temp))
            self.pgm.add_custom_resource("temperature_outside", str(outside_temp))
            
            return True
        return False
    
    def log_motion_detected(self):
        """Log when motion is detected"""
        current_time = time.time()
        
        # Prevent duplicate triggers in short timespan
        if current_time - self.last_alert_time < 2:
            return False
            
        print("Logging motion detection power event")
        self.last_alert_time = current_time
        
        # Make sure measurement is active
        if not self.measurement_active:
            self.start_power_measurement()
            
        # Create a trigger for motion detection
        self.pgm.create_trigger("Motion", "Motion detected")
        
        return True
