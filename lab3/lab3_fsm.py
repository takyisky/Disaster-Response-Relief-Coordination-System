"""
LAB 3: Goals, Events, and Reactive Behavior
Flood Monitoring & Emergency Response System
Agents: SensorAgent, RescueAgent (FSM)
"""

import asyncio
import random
import spade
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State, PeriodicBehaviour
from spade.message import Message
from datetime import datetime

# ─── FSM States ───────────────────────────────────────────────
STATE_IDLE       = "IDLE"
STATE_ASSESSING  = "ASSESSING"
STATE_MONITORING = "MONITORING"
STATE_RESPONDING = "RESPONDING"

# ─── Goals (defined as constants for traceability) ─────────────
GOAL_MONITOR   = "MonitorGoal: Continuously check incoming sensor data"
GOAL_ASSESS    = "AssessGoal: Evaluate severity of detected events"
GOAL_RESCUE    = "RescueGoal: Respond to high-severity flood events"


# ══════════════════════════════════════════════════════════════
#  SENSOR AGENT — periodically generates flood sensor events
# ══════════════════════════════════════════════════════════════
class SensorAgent(Agent):

    class SensorBehaviour(PeriodicBehaviour):
        async def run(self):
            water_level  = random.randint(0, 10)   # metres
            rainfall     = random.randint(0, 200)  # mm/hr
            wind_speed   = random.randint(0, 120)  # km/h

            # Simple severity classification
            if water_level >= 7 or rainfall >= 150:
                severity = "HIGH"
            elif water_level >= 4 or rainfall >= 80:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}] [SensorAgent] Water={water_level}m  "
                  f"Rain={rainfall}mm/hr  Wind={wind_speed}km/h  "
                  f"→ Severity={severity}")

            # Send event to RescueAgent
            msg = Message(to="takyisky.rescue@xmpp.jp")
            msg.set_metadata("performative", "inform")
            msg.set_metadata("ontology", "disaster-event")
            msg.body = f"SEVERITY:{severity};WATER:{water_level};"  \
                       f"RAIN:{rainfall};WIND:{wind_speed}"
            await self.send(msg)

    async def setup(self):
        print("[SensorAgent] Starting — Goal:", GOAL_MONITOR)
        self.add_behaviour(self.SensorBehaviour(period=3))


# ══════════════════════════════════════════════════════════════
#  RESCUE AGENT — FSM reactive behaviour
# ══════════════════════════════════════════════════════════════

# ── State: IDLE ──────────────────────────────────────────────
class IdleState(State):
    async def run(self):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [RescueAgent FSM] State=IDLE  "
              f"(Waiting for disaster events...)")
        msg = await self.receive(timeout=10)
        if msg and msg.get_metadata("ontology") == "disaster-event":
            self.agent.last_event = msg.body
            print(f"[{ts}] [RescueAgent FSM] Event received → ASSESSING")
            self.set_next_state(STATE_ASSESSING)
        else:
            self.set_next_state(STATE_IDLE)


# ── State: ASSESSING ─────────────────────────────────────────
class AssessingState(State):
    async def run(self):
        ts = datetime.now().strftime("%H:%M:%S")
        event = self.agent.last_event
        print(f"[{ts}] [RescueAgent FSM] State=ASSESSING  "
              f"Goal={GOAL_ASSESS}")
        print(f"[{ts}] [RescueAgent FSM] Parsing event → {event}")

        # Parse severity from message body
        parts = dict(p.split(":") for p in event.split(";") if ":" in p)
        severity = parts.get("SEVERITY", "LOW")
        self.agent.severity = severity

        if severity == "HIGH":
            print(f"[{ts}] [RescueAgent FSM] HIGH severity → RESPONDING")
            self.set_next_state(STATE_RESPONDING)
        else:
            print(f"[{ts}] [RescueAgent FSM] {severity} severity → MONITORING")
            self.set_next_state(STATE_MONITORING)


# ── State: MONITORING ────────────────────────────────────────
class MonitoringState(State):
    async def run(self):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [RescueAgent FSM] State=MONITORING  "
              f"(Watching for changes...)")
        msg = await self.receive(timeout=4)
        if msg and msg.get_metadata("ontology") == "disaster-event":
            self.agent.last_event = msg.body
            parts = dict(p.split(":") for p in msg.body.split(";") if ":" in p)
            if parts.get("SEVERITY") == "HIGH":
                print(f"[{ts}] [RescueAgent FSM] Escalation detected → ASSESSING")
                self.set_next_state(STATE_ASSESSING)
            else:
                print(f"[{ts}] [RescueAgent FSM] Conditions stable → IDLE")
                self.set_next_state(STATE_IDLE)
        else:
            print(f"[{ts}] [RescueAgent FSM] No change → IDLE")
            self.set_next_state(STATE_IDLE)


# ── State: RESPONDING ────────────────────────────────────────
class RespondingState(State):
    async def run(self):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [RescueAgent FSM] State=RESPONDING  "
              f"Goal={GOAL_RESCUE}")
        print(f"[{ts}] [RescueAgent FSM] *** DISPATCHING RESCUE TEAM ***")
        print(f"[{ts}] [RescueAgent FSM] Allocating boats, medics, supplies...")
        await asyncio.sleep(2)  # simulate rescue operation time
        print(f"[{ts}] [RescueAgent FSM] Rescue task complete → IDLE")
        self.set_next_state(STATE_IDLE)


# ── RescueAgent wiring ───────────────────────────────────────
class RescueAgent(Agent):
    async def setup(self):
        print("[RescueAgent] Starting FSM — Goals: Monitor / Assess / Rescue")
        self.last_event = None
        self.severity   = None

        fsm = FSMBehaviour()
        fsm.add_state(name=STATE_IDLE,       state=IdleState(),       initial=True)
        fsm.add_state(name=STATE_ASSESSING,  state=AssessingState())
        fsm.add_state(name=STATE_MONITORING, state=MonitoringState())
        fsm.add_state(name=STATE_RESPONDING, state=RespondingState())

        fsm.add_transition(source=STATE_IDLE,       dest=STATE_IDLE)
        fsm.add_transition(source=STATE_IDLE,       dest=STATE_ASSESSING)
        fsm.add_transition(source=STATE_ASSESSING,  dest=STATE_RESPONDING)
        fsm.add_transition(source=STATE_ASSESSING,  dest=STATE_MONITORING)
        fsm.add_transition(source=STATE_MONITORING, dest=STATE_ASSESSING)
        fsm.add_transition(source=STATE_MONITORING, dest=STATE_IDLE)
        fsm.add_transition(source=STATE_RESPONDING, dest=STATE_IDLE)

        self.add_behaviour(fsm)


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
async def main():
    print("=" * 60)
    print("  LAB 3: Flood Response FSM — Starting Agents")
    print("=" * 60)

    rescue = RescueAgent("takyisky.rescue@xmpp.jp", "rescue123")
    sensor = SensorAgent("takyisky.sensor@xmpp.jp", "sensor123")

    await rescue.start()
    await sensor.start()

    print("[Main] Agents running for 30 seconds...")
    await asyncio.sleep(30)

    await sensor.stop()
    await rescue.stop()
    print("[Main] Simulation complete.")

if __name__ == "__main__":
    spade.run(main())