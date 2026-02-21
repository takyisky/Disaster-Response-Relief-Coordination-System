"""
LAB 4: Agent Communication Using FIPA-ACL
Flood Monitoring & Emergency Response System
Performatives: INFORM, REQUEST, AGREE, REFUSE
Agents: SensorAgent, RiskAgent, CoordinatorAgent, RescueAgent
"""

import asyncio
import random
import spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message
from datetime import datetime


def ts():
    return datetime.now().strftime("%H:%M:%S")


def log(agent_name, performative, content, direction=""):
    arrow = f" {direction}" if direction else ""
    print(f"[{ts()}] [{agent_name}]{arrow} <{performative}> {content}")


# ══════════════════════════════════════════════════════════════
#  SENSOR AGENT — INFORMs RiskAgent of conditions
# ══════════════════════════════════════════════════════════════
class SensorAgent(Agent):

    class BroadcastBehaviour(PeriodicBehaviour):
        async def run(self):
            water   = random.randint(0, 10)
            rain    = random.randint(0, 200)
            wind    = random.randint(0, 100)

            body = f"WATER:{water};RAIN:{rain};WIND:{wind}"

            msg = Message(to="takyisky.risk4@xmpp.jp")  # RiskAgent's JID
            msg.set_metadata("performative", "inform")
            msg.set_metadata("ontology",     "sensor-reading")
            msg.set_metadata("language",     "disaster-sl")
            msg.body = body

            log("SensorAgent", "INFORM", f"→ RiskAgent | {body}", "→")
            await self.send(msg)

    async def setup(self):
        print(f"[{ts()}] [SensorAgent] Started")
        self.add_behaviour(self.BroadcastBehaviour(period=4))


# ══════════════════════════════════════════════════════════════
#  RISK AGENT — receives INFORM, sends REQUEST to Coordinator
# ══════════════════════════════════════════════════════════════
class RiskAgent(Agent):

    class AssessBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=6)
            if not msg:
                return

            if msg.get_metadata("ontology") == "sensor-reading":
                parts    = dict(p.split(":") for p in msg.body.split(";") if ":" in p)
                water    = int(parts.get("WATER", 0))
                rain     = int(parts.get("RAIN",  0))

                # Risk classification
                if water >= 7 or rain >= 150:
                    risk  = "CRITICAL"
                    action = "DISPATCH_RESCUE"
                elif water >= 4 or rain >= 80:
                    risk  = "HIGH"
                    action = "ALERT_TEAMS"
                else:
                    risk  = "LOW"
                    action = "CONTINUE_MONITORING"

                log("RiskAgent", "INFORM(recv)", f"← SensorAgent | {msg.body}")
                log("RiskAgent", "Assessment",   f"Risk={risk}  Action={action}")

                # REQUEST CoordinatorAgent to act
                req = Message(to="takyisky.coordinator4@xmpp.jp")
                req.set_metadata("performative", "request")
                req.set_metadata("ontology",     "risk-assessment")
                req.set_metadata("language",     "disaster-sl")
                req.body = f"RISK:{risk};ACTION:{action};WATER:{water};RAIN:{rain}"

                log("RiskAgent", "REQUEST", f"→ CoordinatorAgent | {req.body}", "→")
                await self.send(req)

    async def setup(self):
        print(f"[{ts()}] [RiskAgent] Started")
        self.add_behaviour(self.AssessBehaviour())


# ══════════════════════════════════════════════════════════════
#  COORDINATOR AGENT — receives REQUEST, sends INFORM to Rescue
# ══════════════════════════════════════════════════════════════
class CoordinatorAgent(Agent):

    class CoordinateBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=8)
            if not msg:
                return

            perf = msg.get_metadata("performative")

            # ── Handle incoming REQUEST from RiskAgent ──
            if perf == "request" and msg.get_metadata("ontology") == "risk-assessment":
                parts  = dict(p.split(":") for p in msg.body.split(";") if ":" in p)
                risk   = parts.get("RISK",   "LOW")
                action = parts.get("ACTION", "CONTINUE_MONITORING")

                log("CoordinatorAgent", "REQUEST(recv)", f"← RiskAgent | {msg.body}")

                if risk in ("CRITICAL", "HIGH"):
                    # AGREE and forward task to RescueAgent
                    agree = Message(to=str(msg.sender))
                    agree.set_metadata("performative", "agree")
                    agree.set_metadata("ontology",     "task-confirmation")
                    agree.body = f"ACKNOWLEDGED:DISPATCHING;RISK:{risk}"
                    await self.send(agree)
                    log("CoordinatorAgent", "AGREE", f"→ RiskAgent | {agree.body}", "→")

                    # Inform RescueAgent
                    task = Message(to="takyisky.rescue4@xmpp.jp")
                    task.set_metadata("performative", "inform")
                    task.set_metadata("ontology",     "rescue-task")
                    task.body = f"ACTION:{action};RISK:{risk};WATER:{parts.get('WATER')}"
                    await self.send(task)
                    log("CoordinatorAgent", "INFORM", f"→ RescueAgent | {task.body}", "→")

                else:
                    # REFUSE — risk too low to dispatch
                    refuse = Message(to=str(msg.sender))
                    refuse.set_metadata("performative", "refuse")
                    refuse.set_metadata("ontology",     "task-confirmation")
                    refuse.body = f"REFUSED:RISK_TOO_LOW;RISK:{risk}"
                    await self.send(refuse)
                    log("CoordinatorAgent", "REFUSE", f"→ RiskAgent | {refuse.body}", "→")

            # ── Handle INFORM (status update) from RescueAgent ──
            elif perf == "inform" and msg.get_metadata("ontology") == "rescue-status":
                log("CoordinatorAgent", "INFORM(recv)", f"← RescueAgent | {msg.body}")

    async def setup(self):
        print(f"[{ts()}] [CoordinatorAgent] Started")
        self.add_behaviour(self.CoordinateBehaviour())


# ══════════════════════════════════════════════════════════════
#  RESCUE AGENT — receives task INFORM, sends status INFORM back
# ══════════════════════════════════════════════════════════════
class RescueAgent(Agent):

    class ExecuteBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if not msg:
                return

            if msg.get_metadata("ontology") == "rescue-task":
                log("RescueAgent", "INFORM(recv)", f"← CoordinatorAgent | {msg.body}")

                parts  = dict(p.split(":") for p in msg.body.split(";") if ":" in p)
                action = parts.get("ACTION", "CONTINUE_MONITORING")
                risk   = parts.get("RISK",   "LOW")

                print(f"[{ts()}] [RescueAgent] *** Executing: {action}  (Risk={risk}) ***")
                await asyncio.sleep(1.5)  # simulate execution

                # Send status update back to coordinator
                status = Message(to="takyisky.coordinator4@xmpp.jp")
                status.set_metadata("performative", "inform")
                status.set_metadata("ontology",     "rescue-status")
                status.body = f"STATUS:COMPLETE;ACTION:{action};RISK:{risk}"
                await self.send(status)
                log("RescueAgent", "INFORM", f"→ CoordinatorAgent | {status.body}", "→")

    async def setup(self):
        print(f"[{ts()}] [RescueAgent] Started")
        self.add_behaviour(self.ExecuteBehaviour())


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
async def main():
    print("=" * 65)
    print("  LAB 4: FIPA-ACL Communication — Flood Response System")
    print("  Performatives: INFORM | REQUEST | AGREE | REFUSE")
    print("=" * 65)

    rescue      = RescueAgent(     "takyisky.rescue4@xmpp.jp",      "rescue123")
    coordinator = CoordinatorAgent("takyisky.coordinator4@xmpp.jp", "coord123")
    risk        = RiskAgent(       "takyisky.risk4@xmpp.jp",        "risk123")
    sensor      = SensorAgent(     "takyisky.sensor4@xmpp.jp",      "sensor123")

    # Start in reverse dependency order
    await rescue.start()
    await coordinator.start()
    await risk.start()
    await sensor.start()

    print(f"[{ts()}] [Main] All agents running for 40 seconds...")
    await asyncio.sleep(40)

    await sensor.stop()
    await risk.stop()
    await coordinator.stop()
    await rescue.stop()
    print(f"[{ts()}] [Main] Simulation complete.")

if __name__ == "__main__":
    spade.run(main())