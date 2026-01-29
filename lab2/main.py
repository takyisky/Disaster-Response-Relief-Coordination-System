import asyncio
from environment import DisasterEnvironment
from sensor_agent import SensorAgent

async def main():
    print("=== Lab 2: Disaster Monitoring ===\n")
    
    # Create the environment
    env = DisasterEnvironment()
    
    print("Initial state:")
    for zone, data in env.get_status().items():
        print(f"  {zone}: damage={data['damage']:.1f}, fire={data['fire']}")
    print()
    
    # Create and start the sensor agent
    agent = SensorAgent("sensor@localhost", "password", env)
    await agent.start()
    
    print("Monitoring for 30 seconds...\n")
    
    # Run for 30 seconds
    try:
        await asyncio.sleep(30)
    except KeyboardInterrupt:
        print("\nStopped by user")
    
    # Stop the agent
    await agent.stop()
    
    # Show final results
    print("\n=== Final Report ===")
    print("\nFinal zone status:")
    for zone, data in env.get_status().items():
        status = "CRITICAL" if data['damage'] >= 7 else "OK"
        print(f"  {zone}: {status} (damage={data['damage']:.1f})")
    
    print(f"\nTotal events logged: {len(env.events)}")
    print("\nLast 5 events:")
    for event in env.events[-5:]:
        print(f"  {event}")
    
    # Save to file
    with open('event_log.txt', 'w') as f:
        f.write("Disaster Monitoring Event Log\n")
        f.write("="*40 + "\n\n")
        for event in env.events:
            f.write(event + "\n")
    
    print("\nEvents saved to event_log.txt")

if __name__ == "__main__":
    asyncio.run(main())