import urequests as requests
import ujson as json
import time

class PowerGoblinManager:
    """
    A MicroPython client for interacting with PowerGoblin API from ESP32
    Enables power measurement and monitoring for smart house applications
    """
    def __init__(self, host="localhost:8080"):
        self.host = "http://" + host + "/api/v2/"
        self.session_id = "latest"  # Default to latest session
    
    def _handle_response(self, response):
        """Process API response and extract result data"""
        try:
            if response.status_code != 200:
                print(f"Error: HTTP status {response.status_code}")
                return None
            
            content = response.text
            if content and len(content) > 0:
                try:
                    return json.loads(content).get("result")
                except:
                    return content
            return None
        finally:
            response.close()  # Important to avoid memory leaks in MicroPython
    
    def get(self, url):
        """Send a GET request to the PowerGoblin API"""
        try:
            response = requests.get(self.host + url)
            return self._handle_response(response)
        except Exception as e:
            print(f"GET request error: {e}")
            return None
            
    def post_json(self, url, data):
        """Send a POST request with JSON data to the PowerGoblin API"""
        try:
            response = requests.post(
                self.host + url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(data)
            )
            return self._handle_response(response)
        except Exception as e:
            print(f"POST JSON error: {e}")
            return None
    
    def post_text(self, url, text):
        """Send a POST request with text data to the PowerGoblin API"""
        try:
            response = requests.post(
                self.host + url,
                headers={'Content-Type': 'text/plain'},
                data=text
            )
            return self._handle_response(response)
        except Exception as e:
            print(f"POST text error: {e}")
            return None
    
    # Session management
    def start_session(self):
        """Start a new measurement session"""
        result = self.get("cmd/startSession")
        if result:
            print("New session started")
        return result
    
    def get_session_info(self):
        """Get information about the current session"""
        return self.get(f"session/{self.session_id}")
    
    # Meter management
    def get_meters(self):
        """Get all available meters in the current session"""
        return self.get(f"session/{self.session_id}/meter")
    
    def toggle_meter(self, meter_id):
        """Toggle a specific meter on or off"""
        return self.get(f"session/{self.session_id}/meter/{meter_id}/toggle")
    
    def add_meter(self, meter_id):
        """Add a meter to the current session"""
        return self.get(f"session/{self.session_id}/meter/{meter_id}/add")
    
    def rename_meter_channel(self, meter_id, channel, name):
        """Rename a meter channel for better identification"""
        return self.get(f"session/{self.session_id}/meter/{meter_id}/rename/{channel}/{name}")
    
    # Measurement control
    def start_measurement(self, unit="ESP32", message=""):
        """Start a new measurement from the ESP32"""
        if message:
            return self.post_text(f"session/{self.session_id}/measurement/start/{unit}", message)
        else:
            return self.get(f"session/{self.session_id}/measurement/start/{unit}")
    
    def stop_measurement(self, unit="ESP32", message=""):
        """Stop the current measurement"""
        if message:
            return self.post_text(f"session/{self.session_id}/measurement/stop/{unit}", message)
        else:
            return self.get(f"session/{self.session_id}/measurement/stop/{unit}")
    
    def rename_measurement(self, name):
        """Rename the current measurement"""
        return self.post_text(f"session/{self.session_id}/measurement/rename", name)
    
    # Run control 
    def start_run(self, unit="ESP32", message=""):
        """Start a new run within the current measurement"""
        if message:
            return self.post_text(f"session/{self.session_id}/run/start/{unit}", message)
        else:
            return self.get(f"session/{self.session_id}/run/start/{unit}")
    
    def stop_run(self, unit="ESP32", message=""):
        """Stop the current run"""
        if message:
            return self.post_text(f"session/{self.session_id}/run/stop/{unit}", message)
        else:
            return self.get(f"session/{self.session_id}/run/stop/{unit}")
    
    # Trigger events
    def create_trigger(self, trigger_type, message, unit="ESP32"):
        """Create a trigger event during measurement"""
        trigger_data = {
            "triggerType": trigger_type,
            "unit": unit,
            "message": message,
            "type": "trigger"
        }
        return self.post_json(f"session/{self.session_id}/trigger", trigger_data)
    
    # Power data retrieval
    def get_power_data(self, measurement_id, meter_id, channel):
        """Get power readings for a specific meter and channel"""
        return self.get(f"session/{self.session_id}/logs/power/{measurement_id}/{meter_id}/{channel}")
    
    # Resource management
    def add_custom_resource(self, resource, value, unit="ESP32"):
        """Add custom resource data to the measurement"""
        return self.get(f"session/{self.session_id}/resource/{resource}/add/{value}/{unit}")
    
    def get_resource_data(self, measurement_id, unit, resource):
        """Get resource data for a measurement"""
        return self.get(f"session/{self.session_id}/logs/resource/{measurement_id}/{unit}/{resource}")
