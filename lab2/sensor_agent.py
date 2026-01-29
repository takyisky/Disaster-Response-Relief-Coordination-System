from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
import asyncio

class MonitorBehaviour(CyclicBehaviour):
    async def run(self):
        # Get the environment from the agent
        env = self.agent.environment
        
        # Update the environment state
        env.update()
        
        # Check each zone
        zones = env.get_status()
        for zone_name, zone_data in zones.items():
            damage = zone_data['damage']
            has_fire = zone_data['fire']
            
            # Check if damage is critical
            if damage > 7.0:
                msg = f"CRITICAL: {zone_name} damage level is {damage:.1f}"
                event = env.log_event(msg)
                print(event)
            
            # Check if there's fire
            if has_fire and damage > 5.0:
                msg = f"WARNING: Fire in {zone_name}, damage at {damage:.1f}"
                event = env.log_event(msg)
                print(event)
        
        # Wait 3 seconds before checking again
        await asyncio.sleep(3)


class SensorAgent(Agent):
    def __init__(self, jid, password, environment):
        super().__init__(jid, password)
        self.environment = environment
    
    async def setup(self):
        print("SensorAgent started")
        # Add the monitoring behaviour
        behaviour = MonitorBehaviour()
        self.add_behaviour(behaviour)