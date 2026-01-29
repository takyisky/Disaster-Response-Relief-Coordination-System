import asyncio
import spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour

class DummyAgent(Agent):
    class MyBehav(CyclicBehaviour):
        async def on_start(self):
            print("Starting behaviour...")
            self.counter = 0

        async def run(self):
            print(f"Counter: {self.counter}")
            self.counter += 1
            if self.counter > 3:
                self.kill(exit_code=10)
                return
            await asyncio.sleep(1)

        async def on_end(self):
            print(f"Behaviour finished with exit code {self.exit_code}.")

    async def setup(self):
        print("Agent starting...")
        self.add_behaviour(self.MyBehav())

async def main():
    agent = DummyAgent("takyisky.agent1@xmpp.jp", "agent1")
    await agent.start()

    # Let the agent run for a few seconds
    await asyncio.sleep(6)

    await agent.stop()

if __name__ == "__main__":
    spade.run(main())
