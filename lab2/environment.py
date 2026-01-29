import random
from datetime import datetime

class DisasterEnvironment:
    def __init__(self):
        # Start with 3 zones to keep it simple
        self.zones = {
            'Zone_A': {'damage': 2.0, 'fire': False},
            'Zone_B': {'damage': 4.5, 'fire': True},
            'Zone_C': {'damage': 1.0, 'fire': False}
        }
        self.events = []
    
    def update(self):
        # Make damage get worse over time
        for zone_name in self.zones:
            zone = self.zones[zone_name]
            
            # Fire zones get worse faster
            if zone['fire']:
                zone['damage'] += random.uniform(0.3, 0.8)
            else:
                zone['damage'] += random.uniform(0.1, 0.3)
            
            # Keep damage between 0 and 10
            if zone['damage'] > 10:
                zone['damage'] = 10
    
    def get_status(self):
        return self.zones
    
    def log_event(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        event = f"[{timestamp}] {message}"
        self.events.append(event)
        return event