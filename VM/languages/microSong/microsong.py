#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Microwave MicroSong → MicrowaveVM (.mwasm)

Turn a simple music DSL into VM code where POWER encodes frequency (Hz-ish)
and PRINT produces a tick of tone at that "frequency". Rests set POWER=0
and tick silently.

Syntax (one or more lines; space-separated tokens; comments with '#'):

  tempo <bpm>
  tpb <ticks-per-beat>          # default: 8 (quarter note = 8 ticks)

  # Music tokens:
  C4/4  D#4/8  F3/16  Bb3/4     # notes: [A-G][#|b]?<octave>/<den>
  R/8                          # rest: R/<den>
  |                            # optional bar separator (ignored)

Examples:
  tempo 120
  tpb 8
  C4/4 D4/4 E4/4 F4/4 | G4/2 R/8 G4/8

Compilation model:
- For a NOTE with duration 'ticks':
    SET POWER <freq_code>
    SET TIME ticks
  note_loop:
    DECJZ TIME note_end
    PRINT
    GOTO note_loop
  note_end:

- For a REST with duration 'ticks':
    SET POWER 0
    SET TIME ticks
  rest_loop:
    DECJZ TIME rest_end
    GOTO rest_loop
  rest_end:

- HALT at end (you can remove if you want to chain programs).

Frequency mapping:
- Equal-tempered A4=440Hz. POWER gets int(round(freq_hz)).
- This assumes your microwave treats POWER as "tone frequency". In the
  current VM, PRINT just logs; on real hardware you'd drive a beeper
  at a rate derived from POWER.

Usage:
  python3 microsong_compiler.py song.ms > song.mwasm
  python3 main.py song.mwasm
"""

import re
import sys
from typing import List, Tuple

# -------------------------
# Utilities
# -------------------------

NOTE_INDEX = {"C":0,"D":2,"E":4,"F":5,"G":7,"A":9,"B":11}

def midi_number(note_name: str, accidental: str, octave: int) -> int:
    base = NOTE_INDEX[note_name.upper()]
    if accidental == "#": base += 1
    elif accidental.lower() == "b": base -= 1
    # MIDI: C4 = 60; so C0 = 12. n = 12 + semitone + 12*oct
    return 12 + base + 12*octave

def freq_from_midi(n: int) -> float:
    # A4=440 -> MIDI 69
    return 440.0 * (2.0 ** ((n - 69) / 12.0))

def power_from_freq(freq: float) -> int:
    # simplest: POWER = nearest Hz (int). If too big, you can scale down.
    return int(round(freq))

# -------------------------
# Emitter
# -------------------------

class Asm:
    def __init__(self):
        self.lines: List[str] = []
        self.refs = set()
        self.defs = set()
        self.lab_i = 0

    def new_label(self, hint: str) -> str:
        self.lab_i += 1
        base = re.sub(r"[^A-Za-z0-9_]", "_", hint)
        if not re.match(r"[A-Za-z_]", base): base = "_" + base
        return f"{base}_{self.lab_i}"

    def emit(self, s: str):
        self._track(s)
        self.lines.append(s)

    def label(self, name: str):
        self.lines.append(f"{name}:")
        self.defs.add(name)

    def _track(self, s: str):
        m = re.match(r"\s*DECJZ\s+\w+\s+([A-Za-z_]\w*)\s*$", s)
        if m: self.refs.add(m.group(1))
        m = re.match(r"\s*GOTO\s+([A-Za-z_]\w*)\s*$", s)
        if m: self.refs.add(m.group(1))

    def validate(self):
        missing = sorted(self.refs - self.defs)
        if missing: raise SystemExit(f"Compiler error: undefined labels: {', '.join(missing)}")

    def code(self) -> str:
        return "\n".join(self.lines) + ("\n" if self.lines and not self.lines[-1].endswith("\n") else "")

# -------------------------
# Parser
# -------------------------

Token = Tuple[str, Tuple]  # (op, args)

class Parser:
    def __init__(self, src: str):
        self.src = src
        self.tempo_bpm = 120
        self.tpb = 8

    def parse(self) -> Tuple[List[Token], int, int]:
        toks: List[Token] = []
        for raw in self.src.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line: continue
            if line.lower().startswith("tempo"):
                m = re.match(r"tempo\s+([0-9]+)\s*$", line, re.I)
                if not m: raise SystemExit(f"Bad tempo line: {line}")
                self.tempo_bpm = int(m.group(1))
                continue
            if line.lower().startswith("tpb"):
                m = re.match(r"tpb\s+([0-9]+)\s*$", line, re.I)
                if not m: raise SystemExit(f"Bad tpb line: {line}")
                self.tpb = int(m.group(1))
                if self.tpb <= 0: raise SystemExit("tpb must be > 0")
                continue

            # split tokens by whitespace, ignore bars
            for tok in re.split(r"\s+", line):
                if tok == "|" or tok == "": continue
                # Rest: R/den
                m = re.match(r"^[Rr]/([0-9]+)$", tok)
                if m:
                    den = int(m.group(1))
                    toks.append(("rest", (den,)))
                    continue
                # Note: Name[#|b]?Octave/den
                m = re.match(r"^([A-Ga-g])([#bB]?)(-?[0-9]+)/([0-9]+)$", tok)
                if m:
                    name = m.group(1).upper()
                    acc  = m.group(2)
                    if acc == "B": acc = "b"
                    octave = int(m.group(3))
                    den    = int(m.group(4))
                    toks.append(("note", (name, acc, octave, den)))
                    continue
                # Print temperature
                if tok.lower() == "print_temp":
                    toks.append(("print_temp", ()))
                    continue
                raise SystemExit(f"Bad token: {tok}")

        return toks, self.tempo_bpm, self.tpb

# -------------------------
# Codegen
# -------------------------

class Codegen:
    def __init__(self, tempo_bpm: int, tpb: int):
        self.asm = Asm()
        self.tempo = max(1, tempo_bpm)
        self.tpb = tpb

    def duration_ticks(self, den: int) -> int:
        # quarter note has tpb ticks
        # whole = 4 * tpb; duration = (4/den) * tpb
        if den <= 0: raise SystemExit("Duration denominator must be > 0")
        ticks = (4 * self.tpb) // den
        return max(1, ticks)

    def emit_note(self, name: str, acc: str, octave: int, den: int):
        n = midi_number(name, acc, octave)
        freq = freq_from_midi(n)
        pwr = power_from_freq(freq)
        ticks = self.duration_ticks(den)

        self.asm.emit(f"SET POWER {pwr}")
        self.asm.emit(f"SET TIME {ticks}")
        loop = self.asm.new_label("note")
        end  = self.asm.new_label("end_note")
        self.asm.label(loop)
        self.asm.emit(f"DECJZ TIME {end}")
        # PRINT = one beep tick at this 'frequency'
        self.asm.emit("PRINT")
        self.asm.emit(f"GOTO {loop}")
        self.asm.label(end)

    def emit_rest(self, den: int):
        ticks = self.duration_ticks(den)
        self.asm.emit("SET POWER 0")
        self.asm.emit(f"SET TIME {ticks}")
        loop = self.asm.new_label("rest")
        end  = self.asm.new_label("end_rest")
        self.asm.label(loop)
        self.asm.emit(f"DECJZ TIME {end}")
        self.asm.emit(f"GOTO {loop}")
        self.asm.label(end)

    def compile(self, tokens: List[Token]) -> str:
        # Optional: print tempo/tpb markers at start if you want
        for op, args in tokens:
            if op == "note":
                self.emit_note(*args)
            elif op == "rest":
                (den,) = args
                self.emit_rest(den)
            elif op == "print_temp":
                self.asm.emit("PRINT TEMP")
            else:
                raise SystemExit(f"Internal: unknown token {op}")
        self.asm.emit("HALT")
        self.asm.validate()
        return self.asm.code()

# -------------------------
# CLI + demo
# -------------------------

DEMO = """\
# Twinkle (first phrase, key C), quarter=TPB ticks
tempo 120
tpb 8
C4/4 C4/4 G4/4 G4/4 | A4/4 A4/4 G4/2
F4/4 F4/4 E4/4 E4/4 | D4/4 D4/4 C4/2
"""

def main(argv: List[str]):
    if len(argv) == 2 and argv[1] == "--demo":
        print(DEMO)
        return
    if len(argv) != 2:
        print("Usage: python3 microsong_compiler.py <song.ms>")
        print("       python3 microsong_compiler.py --demo")
        sys.exit(2)

    src = open(argv[1], "r", encoding="utf-8").read()
    tokens, bpm, tpb = Parser(src).parse()
    asm = Codegen(bpm, tpb).compile(tokens)
    sys.stdout.write(asm)

if __name__ == "__main__":
    main(sys.argv)
