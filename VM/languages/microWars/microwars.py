#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MicroWars → MicrowaveVM (.mwasm)

A tiny battle scripting language for a 2-register + stack VM.
We support exactly TWO units (names arbitrary), with:
  unit "Name" health H attack A

Script:
  start_battle
  attack "Attacker" -> "Defender" repeat N
  special "Unit" heal K
  end_battle

Example:
  unit "Warrior" health 50 attack 7
  unit "Mage"    health 30 attack 10

  start_battle
  attack "Warrior" -> "Mage" repeat 3
  attack "Mage"    -> "Warrior" repeat 2
  special "Mage" heal 5
  attack "Warrior" -> "Mage" repeat 4
  end_battle

Semantics (fits the VM):
- We keep the two units' health on the VM stack, always in a fixed order.
- Top-of-stack and second-of-stack are accessible by swapping (pop/pop/push/push).
- An attack of strength A does up to A ticks of damage:
    Each tick:
      - If defender health==0 → stop.
      - Else decrement defender health by 1 and PRINT (hit beep).
- Heal K increments the target's health by K.
- Everything compiles to plain VM ops: SET/INC/DECJZ/GOTO/PRINT/PUSH/POP/HALT.

Usage:
  python3 microwars_compiler.py battle.mwrs > battle.mwasm
  python3 main.py battle.mwasm
"""

import re
import sys
from dataclasses import dataclass
from typing import List, Tuple, Dict

# ------------ Assembly emitter with labels ------------

class Asm:
    def __init__(self):
        self.lines: List[str] = []
        self.defs = set()
        self.refs = set()
        self.i = 0
    def new_label(self, hint: str) -> str:
        self.i += 1
        base = re.sub(r"[^A-Za-z0-9_]", "_", hint)
        if not re.match(r"[A-Za-z_]", base): base = "_" + base
        return f"{base}_{self.i}"
    def label(self, name: str):
        self.lines.append(f"{name}:"); self.defs.add(name)
    def emit(self, s: str):
        # track label refs for validation
        m = re.match(r"\s*DECJZ\s+\w+\s+([A-Za-z_]\w*)\s*$", s)
        if m: self.refs.add(m.group(1))
        m = re.match(r"\s*GOTO\s+([A-Za-z_]\w*)\s*$", s)
        if m: self.refs.add(m.group(1))
        self.lines.append(s)
    def validate(self):
        missing = sorted(self.refs - self.defs)
        if missing: raise SystemExit(f"Compiler error: undefined labels: {', '.join(missing)}")
    def code(self) -> str:
        return "\n".join(self.lines) + ("\n" if self.lines and not self.lines[-1].endswith("\n") else "")

# ------------ DSL structures ------------

@dataclass
class Unit:
    name: str
    health: int
    attack: int

Token = Tuple[str, Tuple]

class Parser:
    def __init__(self, src: str):
        self.src = src
        self.units: Dict[str, Unit] = {}
        self.script: List[Token] = []

    def parse(self):
        for raw in self.src.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"): 
                continue

            # unit "Name" health H attack A
            m = re.match(r'^unit\s+"([^"]+)"\s+health\s+([0-9]+)\s+attack\s+([0-9]+)\s*$', line, re.I)
            if m:
                name = m.group(1)
                H = int(m.group(2))
                A = int(m.group(3))
                if name in self.units:
                    raise SystemExit(f'Duplicate unit name: "{name}"')
                self.units[name] = Unit(name=name, health=H, attack=A)
                continue

            if line.lower() == "start_battle":
                self.script.append(("start", ()))
                continue
            if line.lower() == "end_battle":
                self.script.append(("end", ()))
                continue

            # attack "A" -> "B" repeat N
            m = re.match(r'^attack\s+"([^"]+)"\s*->\s*"([^"]+)"\s*(?:repeat\s+([0-9]+))?\s*$', line, re.I)
            if m:
                a = m.group(1); b = m.group(2); n = m.group(3)
                n = int(n) if n else 1
                self.script.append(("attack", (a, b, n)))
                continue

            # special "X" heal K
            m = re.match(r'^special\s+"([^"]+)"\s+heal\s+([0-9]+)\s*$', line, re.I)
            if m:
                who = m.group(1); k = int(m.group(2))
                self.script.append(("heal", (who, k)))
                continue

            # special "X" show_weight
            m = re.match(r'^special\s+"([^"]+)"\s+show_weight\s*$', line, re.I)
            if m:
                who = m.group(1)
                self.script.append(("show_weight", (who,)))
                continue

            raise SystemExit(f"Unknown syntax: {line}")

        if len(self.units) != 2:
            raise SystemExit("Exactly two units must be declared.")

        return self.units, self.script

# ------------ Code generator ------------

class Codegen:
    def __init__(self, units: Dict[str, Unit], script: List[Token]):
        # Fix an order for the two units → stack layout: [U1 (bottom), U2 (top)]
        self.u1, self.u2 = sorted(units.values(), key=lambda u: u.name)
        self.units = {self.u1.name: self.u1, self.u2.name: self.u2}
        self.script = script
        self.asm = Asm()

    # --- stack helpers (top/second only) ---

    def swap_top_second(self):
        # POP TIME ; POP POWER ; PUSH TIME ; PUSH POWER
        self.asm.emit("POP TIME")
        self.asm.emit("POP POWER")
        self.asm.emit("PUSH TIME")
        self.asm.emit("PUSH POWER")

    def pop_top_into_TIME(self):
        self.asm.emit("POP TIME")

    def push_TIME(self):
        self.asm.emit("PUSH TIME")

    # --- primitives ---

    def set_reg(self, r: str, n: int):
        self.asm.emit(f"SET {r} {int(n)}")

    def inc_time(self, k: int):
        for _ in range(k):
            self.asm.emit("INC TIME")

    # --- domain actions ---

    def load_defender_health_into_TIME(self, defender: str):
        # Stack order is always [u1, u2] (bottom..top).
        # If defender is top (u2) → POP TIME.
        # If defender is second (u1) → swap, POP TIME, later push & swap back.
        if defender == self.u2.name:
            self.pop_top_into_TIME()
            return "top"
        elif defender == self.u1.name:
            self.swap_top_second()
            self.pop_top_into_TIME()
            return "second"
        else:
            raise SystemExit(f'Unknown unit: "{defender}"')

    def store_TIME_back_and_restore_order(self, pos_marker: str):
        # Push updated health back; undo swap if needed to restore original order.
        self.push_TIME()
        if pos_marker == "second":
            self.swap_top_second()

    def emit_attack_once(self, attacker: Unit, defender: Unit):
        # 1) Bring defender health into TIME (remember if it was top/second).
        pos = self.load_defender_health_into_TIME(defender.name)

        # 2) Damage loop: POWER counts remaining damage; TIME is defender health
        self.set_reg("POWER", attacker.attack)
        loop = self.asm.new_label(f"atk_{attacker.name}_to_{defender.name}")
        done = self.asm.new_label("atk_done")
        self.asm.label(loop)
        # consume one damage tick
        self.asm.emit(f"DECJZ POWER {done}")
        # if health==0, jump to done (no underflow)
        self.asm.emit(f"DECJZ TIME {done}")
        # hit beep
        self.asm.emit("PRINT")
        self.asm.emit(f"GOTO {loop}")
        self.asm.label(done)

        # 3) Store updated health back to stack and restore order
        self.store_TIME_back_and_restore_order(pos)

    def emit_heal(self, who: Unit, k: int):
        pos = self.load_defender_health_into_TIME(who.name)  # reuse same accessor
        self.inc_time(k)
        self.store_TIME_back_and_restore_order(pos)

    def compile(self) -> str:
        a = self.asm

        # Prologue: push initial healths in fixed order [u1, u2]
        # We do this at 'start_battle', not at top-level, so that scripts can define units first.
        started = False

        for op, args in self.script:
            if op == "start":
                if started:
                    raise SystemExit("start_battle specified more than once.")
                started = True
                # push u1 health, then u2 health (u2 ends up on top)
                self.set_reg("TIME", self.u1.health); self.push_TIME()
                self.set_reg("TIME", self.u2.health); self.push_TIME()

            elif op == "attack":
                if not started: raise SystemExit("Use start_battle before actions.")
                attacker_name, defender_name, n = args
                if attacker_name not in self.units or defender_name not in self.units:
                    raise SystemExit("Unknown unit in attack.")
                att = self.units[attacker_name]; dfn = self.units[defender_name]
                # Unroll repeat n vezes no momento da compilação para evitar conflito com uso de TIME dentro do ataque.
                # Se n == 0, não gera nada (defensivo, ainda que repeat 0 raramente seja usado).
                for _ in range(n):
                    self.emit_attack_once(att, dfn)

            elif op == "heal":
                if not started: raise SystemExit("Use start_battle before actions.")
                who_name, k = args
                if who_name not in self.units:
                    raise SystemExit("Unknown unit in heal.")
                self.emit_heal(self.units[who_name], k)

            elif op == "show_weight":
                self.asm.emit("PRINT WEIGHT")
            elif op == "end":
                a.emit("HALT")

            else:
                raise SystemExit(f"Internal: unknown token {op}")

        if not started:
            raise SystemExit("Script missing start_battle.")
        # Ensure HALT exists; if not provided by user, add one.
        if not any(line.strip() == "HALT" for line in a.lines):
            a.emit("HALT")

        a.validate()
        return a.code()

# ------------ CLI ------------

DEMO = """\
# Demo battle
unit "Warrior" health 50 attack 7
unit "Mage"    health 30 attack 10

start_battle
attack "Warrior" -> "Mage" repeat 3
attack "Mage"    -> "Warrior" repeat 2
special "Mage" heal 5
attack "Warrior" -> "Mage" repeat 4
end_battle
"""

def main(argv: List[str]):
    if len(argv) == 2 and argv[1] == "--demo":
        print(DEMO); return
    if len(argv) != 2:
        print("Usage: python3 microwars_compiler.py <script.mwrs>")
        print("       python3 microwars_compiler.py --demo")
        sys.exit(2)

    src = open(argv[1], "r", encoding="utf-8").read()
    units, script = Parser(src).parse()
    asm = Codegen(units, script).compile()
    sys.stdout.write(asm)

if __name__ == "__main__":
    main(sys.argv)
