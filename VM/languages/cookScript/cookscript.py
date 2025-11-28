#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CookScript → MicrowaveVM (.mwasm)

A tiny “microwave recipe” DSL that compiles to your two-register VM with a stack.

Supported syntax (one statement per line; numbers are non-negative integers):

  power <n>                     # set POWER (0..100 is a good convention)
  cook <t>                      # run a t-second timer (TIME counts down)
  rest <t>                      # power 0 + t-second timer
  beep                          # PRINT, preserving TIME
  repeat <n> {                  # repeat a block n times (safe with cook)
    ...                         #   body
  }                             # end repeat
  every <k> seconds beep during <t> seconds
  stage "<name>" {              # purely cosmetic grouping with a marker beep
    ...
  }

Sugar:
  defrost <t>   == power 30 ; cook <t>
  reheat  <t>   == power 70 ; cook <t>
  full    <t>   == power 100; cook <t>

CLI:
  python3 cookscript.py recipe.cs > recipe.mwasm
"""

import re
import sys
from typing import List, Tuple

# ------------------------------
# Assembly emitter & label gensym
# ------------------------------

class Asm:
    def __init__(self):
        self.lines: List[str] = []
        self.defs = set()
        self.refs = set()

    def emit(self, s: str):
        self._track_refs(s)
        self.lines.append(s)

    def label(self, name: str):
        self.lines.append(f"{name}:")
        self.defs.add(name)

    def code(self) -> str:
        return "\n".join(self.lines) + ("\n" if self.lines and not self.lines[-1].endswith("\n") else "")

    def validate(self):
        missing = sorted(self.refs - self.defs)
        if missing:
            raise SystemExit(f"Compiler error: undefined labels: {', '.join(missing)}")

    def _track_refs(self, s: str):
        m = re.match(r"\s*DECJZ\s+\w+\s+([A-Za-z_]\w*)\s*$", s)
        if m: self.refs.add(m.group(1))
        m = re.match(r"\s*GOTO\s+([A-Za-z_]\w*)\s*$", s)
        if m: self.refs.add(m.group(1))

class Gensym:
    def __init__(self):
        self.i = 0
    def new(self, hint: str) -> str:
        self.i += 1
        base = re.sub(r"[^A-Za-z0-9_]", "_", hint)
        if not re.match(r"[A-Za-z_]", base): base = "_" + base
        return f"{base}_{self.i}"

# ------------------------------
# VM macros (only legal ISA ops)
# ------------------------------

class VM:
    def __init__(self, asm: Asm, gs: Gensym):
        self.a, self.gs = asm, gs

    # primitives
    def SET(self, r, n): self.a.emit(f"SET {r} {int(n)}")
    def INC(self, r, k=1):
        for _ in range(int(k)): self.a.emit(f"INC {r}")
    def DECJZ(self, r, L): self.a.emit(f"DECJZ {r} {L}")
    def GOTO(self, L): self.a.emit(f"GOTO {L}")
    def PRINT(self): self.a.emit("PRINT")
    def PUSH(self, r): self.a.emit(f"PUSH {r}")
    def POP(self, r):  self.a.emit(f"POP {r}")
    def HALT(self):    self.a.emit("HALT")

    # helpers

    # Non-destructive beep (preserve TIME)
    def BEEP(self):
        self.PUSH("TIME")
        self.PRINT()
        self.POP("TIME")

    # Cook: TIME := t; while TIME>0 { DECJZ TIME end; GOTO loop }
    def COOK(self, t: int):
        loop = self.gs.new("cook")
        end  = self.gs.new("end_cook")
        self.SET("TIME", t)
        self.a.label(loop)
        self.DECJZ("TIME", end)
        self.GOTO(loop)
        self.a.label(end)

    # Rest: power 0 + cook t
    def REST(self, t: int):
        self.SET("POWER", 0)
        self.COOK(t)

# ------------------------------
# Parser
# ------------------------------

Token = Tuple[str, Tuple]

class Parser:
    def __init__(self, src: str):
        self.src = src

    def parse(self) -> List[Token]:
        toks: List[Token] = []
        lines = self.src.splitlines()
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            if line == "}":
                toks.append(("end_block", ()))
                continue

            # stage "Name" {
            m = re.match(r'^stage\s+"([^"]+)"\s*\{\s*$', line, re.I)
            if m:
                toks.append(("stage_begin", (m.group(1),)))
                continue

            # repeat n {
            m = re.match(r"^repeat\s+([0-9]+)\s*\{\s*$", line, re.I)
            if m:
                toks.append(("repeat_begin", (int(m.group(1)),)))
                continue

            # every k seconds beep during t seconds   (single-line form)
            m = re.match(r"^every\s+([0-9]+)\s+seconds\s+beep\s+during\s+([0-9]+)\s+seconds\s*$", line, re.I)
            if m:
                toks.append(("every_beep", (int(m.group(1)), int(m.group(2)))))
                continue

            # power n
            m = re.match(r"^power\s+([0-9]+)\s*$", line, re.I)
            if m:
                toks.append(("power", (int(m.group(1)),)))
                continue

            # cook t
            m = re.match(r"^cook\s+([0-9]+)\s*$", line, re.I)
            if m:
                toks.append(("cook", (int(m.group(1)),)))
                continue

            # rest t
            m = re.match(r"^rest\s+([0-9]+)\s*$", line, re.I)
            if m:
                toks.append(("rest", (int(m.group(1)),)))
                continue

            # sugar
            m = re.match(r"^defrost\s+([0-9]+)\s*$", line, re.I)
            if m:
                toks.append(("defrost", (int(m.group(1)),)))
                continue
            m = re.match(r"^reheat\s+([0-9]+)\s*$", line, re.I)
            if m:
                toks.append(("reheat", (int(m.group(1)),)))
                continue
            m = re.match(r"^full\s+([0-9]+)\s*$", line, re.I)
            if m:
                toks.append(("full", (int(m.group(1)),)))
                continue

            # beep
            if line.lower() == "beep":
                toks.append(("beep", ()))
                continue

            # save/restore (optional convenience)
            if line.lower() == "save_power":
                toks.append(("save_power", ())); continue
            if line.lower() == "restore_power":
                toks.append(("restore_power", ())); continue
            if line.lower() == "save_time":
                toks.append(("save_time", ())); continue
            if line.lower() == "restore_time":
                toks.append(("restore_time", ())); continue

            # halt (optional)
            if line.lower() == "halt":
                toks.append(("halt", ()))
                continue

            raise SystemExit(f"Unknown syntax: {line}")

        return toks

# ------------------------------
# Code generator
# ------------------------------

class Codegen:
    def __init__(self):
        self.asm = Asm()
        self.gs  = Gensym()
        self.vm  = VM(self.asm, self.gs)
        self.block_stack: List[Tuple[str, tuple]] = []  # (kind, data)

    def compile(self, tokens: List[Token]) -> str:
        for op, args in tokens:
            if op == "power":
                (p,) = args
                self.vm.SET("POWER", p)

            elif op == "cook":
                (t,) = args
                self.vm.COOK(t)

            elif op == "rest":
                (t,) = args
                self.vm.REST(t)

            elif op == "beep":
                self.vm.BEEP()

            elif op == "save_power":
                self.vm.PUSH("POWER")
            elif op == "restore_power":
                self.vm.POP("POWER")
            elif op == "save_time":
                self.vm.PUSH("TIME")
            elif op == "restore_time":
                self.vm.POP("TIME")

            elif op == "defrost":
                (t,) = args
                self.vm.SET("POWER", 30); self.vm.COOK(t)
            elif op == "reheat":
                (t,) = args
                self.vm.SET("POWER", 70); self.vm.COOK(t)
            elif op == "full":
                (t,) = args
                self.vm.SET("POWER", 100); self.vm.COOK(t)

            elif op == "stage_begin":
                (name,) = args
                # marker: a short double-beep (TIME-preserving)
                self.vm.BEEP(); self.vm.BEEP()
                self.block_stack.append(("stage", (name,)))  # purely structural

            elif op == "repeat_begin":
                (n,) = args
                # TIME will be the iteration counter, but the body may use TIME (cook).
                # Pattern: push TIME, compile body, pop TIME, then DECJZ TIME end.
                start = self.gs.new("repeat")
                end   = self.gs.new("end_repeat")
                self.vm.SET("TIME", n)
                self.asm.label(start)
                # Save iteration count while body runs:
                self.vm.PUSH("TIME")
                self.block_stack.append(("repeat", (start, end)))

            elif op == "every_beep":
                k, t = args
                # Use TIME as main timer and POWER as the k-subcounter.
                # This clobbers POWER during the loop (OK for our model).
                start = self.gs.new("every")
                end   = self.gs.new("end_every")
                hook  = self.gs.new("hook")
                self.vm.SET("TIME", t)
                self.vm.SET("POWER", k)
                self.asm.label(start)
                self.vm.DECJZ("TIME", end)     # each second
                self.vm.DECJZ("POWER", hook)   # sub-counter hits 0?
                self.vm.GOTO(start)
                self.asm.label(hook)
                self.vm.BEEP()
                self.vm.SET("POWER", k)        # reset sub-counter
                self.vm.GOTO(start)
                self.asm.label(end)

            elif op == "end_block":
                if not self.block_stack:
                    raise SystemExit("'}' without an open block")

                kind, data = self.block_stack.pop()

                if kind == "repeat":
                    start, end = data
                    # Body finished; restore iteration count and consume one
                    self.vm.POP("TIME")
                    self.vm.DECJZ("TIME", end)
                    self.vm.GOTO(start)
                    self.asm.label(end)

                elif kind == "stage":
                    # nothing special to close a stage
                    pass

                else:
                    raise SystemExit(f"Internal error: unknown block kind {kind}")

            elif op == "halt":
                self.vm.HALT()

            else:
                raise SystemExit(f"Internal error: unknown token {op}")

        if self.block_stack:
            raise SystemExit("Unclosed block(s) at end of file")

        self.asm.validate()
        return self.asm.code()

# ------------------------------
# CLI + demo recipes
# ------------------------------

DEMO_POPCORN = """
# Popcorn: 2:00 at 80%, beep every 20s, final beep
power 80
every 20 seconds beep during 120 seconds
beep
halt
""".strip()

DEMO_STIR_CYCLES = """
# 3 stir cycles: 45s@70% → beep → rest 10s
repeat 3 {
  power 70
  cook 45
  beep
  rest 10
}
halt
""".strip()

DEMO_DEFROST = """
# Defrost profile: 3× 60s at 30/40/50 with beeps
stage "Defrost 30%" {
  power 30
  cook 60
  beep
}
stage "Defrost 40%" {
  power 40
  cook 60
  beep
}
stage "Defrost 50%" {
  power 50
  cook 60
  beep
}
halt
""".strip()

def main(argv: List[str]):
    if len(argv) == 2 and argv[1] == "--demo":
        print("=== popcorn.cs ===\n" + DEMO_POPCORN)
        print("\n=== stir_cycles.cs ===\n" + DEMO_STIR_CYCLES)
        print("\n=== defrost.cs ===\n" + DEMO_DEFROST)
        return

    if len(argv) != 2:
        print("Usage: python3 microscript_compiler.py <recipe.cs>")
        print("       python3 microscript_compiler.py --demo   # show example scripts")
        sys.exit(2)

    src = open(argv[1], "r", encoding="utf-8").read()
    tokens = Parser(src).parse()
    asm = Codegen().compile(tokens)
    sys.stdout.write(asm)

if __name__ == "__main__":
    main(sys.argv)
