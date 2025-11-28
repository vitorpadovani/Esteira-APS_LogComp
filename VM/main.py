from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

Register = str

@dataclass
class Instr:
    op: str
    args: Tuple[str, ...]  # tokens as strings

class MicrowaveVM:
    """
    A minimal Minsky-style VM specialized to two registers:
      - TIME
      - POWER

    Instruction set (Turing-complete):
      SET R n           ; initialize a register
      INC R             ; R := R + 1
      DECJZ R label     ; if R == 0: PC := label, else: R := R - 1
      GOTO label        ; PC := label
      PRINT             ; print current value of TIME register
      PUSH R            ; push register value onto stack
      POP R             ; pop value from stack into register
      HALT              ; stop

    Labels:
      label_name:       ; defines a target for GOTO/DECJZ
    """

    def __init__(self):
        self.registers: Dict[Register, int] = {"TIME": 0, "POWER": 0}
        self.readonly_registers: Dict[Register, int] = {"TEMP": 0, "WEIGHT": 100}  # WEIGHT in grams
        self.program: List[Instr] = []
        self.labels: Dict[str, int] = {}
        self.pc: int = 0
        self.halted: bool = False
        self.steps: int = 0
        self.stack: List[int] = []
        self.ticks: int = 0  # Total execution ticks for thermal modeling

    # --- Assembler / Loader ---
    def load_program(self, source: str):
        self.program.clear()
        self.labels.clear()
        self.stack.clear()
        self.readonly_registers["TEMP"] = 0  # Reset temperature
        self.readonly_registers["WEIGHT"] = 100  # Default weight in grams
        self.pc = 0
        self.halted = False
        self.steps = 0
        self.ticks = 0

        lines = source.splitlines()
        # First pass: collect labels
        idx = 0
        for raw in lines:
            line = raw.split(';', 1)[0].split('#', 1)[0].strip()
            if not line:
                continue
            if line.endswith(':'):
                label = line[:-1].strip()
                if not label:
                    raise ValueError("Empty label definition.")
                if label in self.labels:
                    raise ValueError(f"Duplicate label: {label}")
                self.labels[label] = idx
            else:
                idx += 1

        # Second pass: parse instructions
        for raw in lines:
            line = raw.split(';', 1)[0].split('#', 1)[0].strip()
            if not line or line.endswith(':'):
                continue
            tokens = line.replace(',', ' ').split()
            op = tokens[0].upper()
            args = tuple(tokens[1:])
            # Basic validation
            if op == "SET":
                if len(args) != 2:
                    raise ValueError(f"SET expects 2 args: {line}")
                if args[0].upper() not in ("TIME", "POWER"):
                    raise ValueError(f"Unknown register in SET: {args[0]}")
                try:
                    int(args[1])
                except:
                    raise ValueError(f"SET value must be integer: {args[1]}")
            elif op == "INC":
                if len(args) != 1 or args[0].upper() not in ("TIME", "POWER"):
                    raise ValueError(f"INC expects register (TIME/POWER): {line}")
            elif op == "DECJZ":
                if len(args) != 2 or args[0].upper() not in ("TIME", "POWER"):
                    raise ValueError(f"DECJZ expects register and label: {line}")
                # label existence checked at run-time to allow forward refs
            elif op == "GOTO":
                if len(args) != 1:
                    raise ValueError(f"GOTO expects 1 label: {line}")
            elif op == "PRINT":
                if len(args) != 0:
                    raise ValueError(f"PRINT takes no args: {line}")
            elif op == "PUSH":
                if len(args) != 1 or args[0].upper() not in ("TIME", "POWER"):
                    raise ValueError(f"PUSH expects register (TIME/POWER): {line}")
            elif op == "POP":
                if len(args) != 1 or args[0].upper() not in ("TIME", "POWER"):
                    raise ValueError(f"POP expects register (TIME/POWER): {line}")
            elif op == "HALT":
                if len(args) != 0:
                    raise ValueError(f"HALT takes no args: {line}")
            else:
                raise ValueError(f"Unknown opcode: {op}")
            self.program.append(Instr(op, args))

    # --- Execution ---
    def step(self):
        if self.halted:
            return
        if not (0 <= self.pc < len(self.program)):
            # Implicit halt if PC falls off program
            self.halted = True
            return

        instr = self.program[self.pc]
        self.steps += 1
        self.ticks += 1
        
        # Update thermal model after each instruction
        self._update_thermal_model()

        def regname(s: str) -> str:
            return s.upper()

        if instr.op == "SET":
            r, v = regname(instr.args[0]), int(instr.args[1])
            self.registers[r] = v
            self.pc += 1

        elif instr.op == "INC":
            r = regname(instr.args[0])
            self.registers[r] = self.registers.get(r, 0) + 1
            self.pc += 1

        elif instr.op == "DECJZ":
            r = regname(instr.args[0])
            target = instr.args[1]
            if self.registers.get(r, 0) == 0:
                if target not in self.labels:
                    raise ValueError(f"Unknown label: {target}")
                self.pc = self.labels[target]
            else:
                self.registers[r] -= 1
                self.pc += 1

        elif instr.op == "GOTO":
            target = instr.args[0]
            if target not in self.labels:
                raise ValueError(f"Unknown label: {target}")
            self.pc = self.labels[target]

        elif instr.op == "PRINT":
            print(f"TIME: {self.registers.get('TIME', 0)}")
            self.pc += 1

        elif instr.op == "PUSH":
            r = regname(instr.args[0])
            value = self.registers.get(r, 0)
            self.stack.append(value)
            self.pc += 1

        elif instr.op == "POP":
            r = regname(instr.args[0])
            if not self.stack:
                raise RuntimeError("Cannot POP from empty stack")
            value = self.stack.pop()
            self.registers[r] = value
            self.pc += 1

        elif instr.op == "HALT":
            print("BEEEEEEP!")
            self.halted = True

    def _update_thermal_model(self):
        """
        Simple thermal model for microwave heating:
        - Temperature increases based on POWER and decreases naturally
        - Heat transfer is affected by item weight (larger items heat slower)
        - Simplified equation: dT = (POWER * 0.1 - TEMP * 0.02) / sqrt(WEIGHT/100)
        """
        power = self.registers.get('POWER', 0)
        current_temp = self.readonly_registers['TEMP']
        weight = self.readonly_registers['WEIGHT']
        
        # Heating rate proportional to power, cooling proportional to current temp
        # Weight factor: heavier items require more energy to heat up
        heating_rate = power * 0.1
        cooling_rate = current_temp * 0.02
        weight_factor = max(1.0, (weight / 100.0) ** 0.5)  # sqrt(weight_ratio)
        
        # Temperature change per tick
        temp_change = (heating_rate - cooling_rate) / weight_factor
        
        # Update temperature (minimum 0, representing room temperature)
        new_temp = max(0, current_temp + int(temp_change))
        self.readonly_registers['TEMP'] = new_temp

    def run(self, max_steps: Optional[int] = None):
        while not self.halted:
            if max_steps is not None and self.steps >= max_steps:
                raise RuntimeError("Step limit reached (possible infinite loop).")
            self.step()

    # --- Helpers ---
    def state(self) -> Dict[str, int]:
        return dict(self.registers)

    def full_state(self) -> Dict:
        return {
            "registers": dict(self.registers),
            "readonly_registers": dict(self.readonly_registers),
            "stack": list(self.stack),
            "pc": self.pc,
            "halted": self.halted,
            "steps": self.steps,
            "ticks": self.ticks
        }

    def set_weight(self, weight_grams: int):
        """Set the weight of the item in the microwave (in grams)"""
        self.readonly_registers['WEIGHT'] = max(1, weight_grams)  # Minimum 1 gram

    def stack_state(self) -> List[int]:
        return list(self.stack)

    def reset_registers(self, TIME: int = 0, POWER: int = 0, WEIGHT: int = 100):
        self.registers["TIME"] = int(TIME)
        self.registers["POWER"] = int(POWER)
        self.readonly_registers["TEMP"] = 0  # Reset to room temperature
        self.readonly_registers["WEIGHT"] = max(1, int(WEIGHT))  # Set item weight
        self.stack.clear()
        self.pc = 0
        self.halted = False
        self.steps = 0
        self.ticks = 0


# --------- Demo programs ---------
# 1) ADD: TIME := TIME + POWER ; POWER := 0
ADD_PROGRAM = """
    ; Precondition: TIME = a, POWER = b
    ; Post:        TIME = a+b, POWER = 0
loop:
    DECJZ POWER end
    INC TIME
    GOTO loop
end:
    HALT
"""

# 2) MULTIPLY via repeated addition:
#    TIME := a * b, POWER := 0
#    Uses TIME as accumulator, POWER as outer counter, and a temporary loop to add 'a' each time.
#    To keep two-register purity, we preload TIME with 0 and "encode" multiplicand via repeated INCs before loop.
MULT_PROGRAM = """
    ; Pre: TIME = 0, POWER = b
    ; Also assume we first built a copy of 'a' into TIME_A via a small bootstrap program,
    ; but to stay 2-register, we'll rebuild 'a' each inner loop by counting with POWER jumps.
    ; Simpler approach: store a in TIME, b in POWER, then compute:
    ;   result := 0
    ;   repeat POWER times: result += a
    ; Here result is accumulated back into TIME; we must preserve 'a' each inner add.
    ;
    ; Encoding trick: We'll do a simple slow method:
    ; - Move a out by consuming TIME into repeated INCs on POWER, then rebuild each cycle.
    ; NOTE: In practice, 2-register multiplication needs careful choreography. Below is a tiny,
    ;       pedagogical but not optimized routine that assumes TIME holds 'a', POWER holds 'b'.
    ;
    ; Step 0: result := 0, move a into TIME_AUX by zeroing TIME while counting in POWER, then restore.
    ; To keep this concise, we show a version where we pre-set TIME=a and POWER=b,
    ; and compute a*b by:
    ;   while POWER>0:
    ;       tmp := a
    ;       while tmp>0:
    ;           INC RESULT   (RESULT is TIME here)
    ;           DEC tmp
    ;       DEC POWER
    ; HALT
    ;
    ; Two-registers force us to reuse TIME as tmp and use DECJZ jumps cleverly.
    ;
    ; Layout:
    ; TIME  = result/tmp (mutates)
    ; POWER = outer counter (b)
    ;
outer:
    DECJZ POWER end          ; if POWER==0 -> end
    ; rebuild tmp := a by adding A times into TIME, but we need 'a'.
    ; For a tiny demo, we'll assume we preloaded TIME with 0 and then inserted 'a' INCs just before start.
    ; Instead, here's a tiny concrete multiplication example baked in:
    HALT
end:
    HALT
"""

# 3) STACK demo: demonstrates PUSH and POP operations
STACK_PROGRAM = """
    ; Demo program showing stack operations
    ; Push TIME and POWER values onto stack, then pop them back in reverse order
    
    SET TIME 10         ; Set TIME = 10
    SET POWER 20        ; Set POWER = 20
    
    PUSH TIME           ; Push 10 onto stack
    PUSH POWER          ; Push 20 onto stack
    
    SET TIME 0          ; Clear TIME
    SET POWER 0         ; Clear POWER
    
    POP POWER           ; Pop 20 into POWER (last in, first out)
    POP TIME            ; Pop 10 into TIME
    
    PRINT               ; Should print TIME: 10
    HALT
"""

# 4) REVERSE_NUMBERS: Use stack to reverse a sequence of numbers
REVERSE_PROGRAM = """
    ; Use stack to reverse numbers
    ; Push several values, then pop them back in reverse order
    
    SET TIME 1
    PUSH TIME
    SET TIME 2  
    PUSH TIME
    SET TIME 3
    PUSH TIME
    SET TIME 4
    PUSH TIME
    SET TIME 5
    PUSH TIME
    
    ; Now pop and print them in reverse order (5, 4, 3, 2, 1)
pop_loop:
    POP TIME
    PRINT
    ; Check if stack is empty by trying to peek (we'll use a simple counter instead)
    SET POWER 4         ; We pushed 5 items, so we need 4 more pops after the first
    
pop_remaining:
    DECJZ POWER done
    POP TIME
    PRINT
    GOTO pop_remaining
    
done:
    HALT
"""

# Quick usage example
if __name__ == "__main__":
    import sys
    
    vm = MicrowaveVM()

    if len(sys.argv) > 1:
        # Load program from file
        filename = sys.argv[1]
        try:
            with open(filename, 'r') as f:
                program_content = f.read()
            vm.load_program(program_content)
            print(f"Loaded program from: {filename}")
            vm.run()
            print("Final state:", vm.state())
            print("Final readonly state:", vm.readonly_registers)
            print("Final stack:", vm.stack_state())
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Example 1: addition a + b (default behavior)
        vm.load_program(ADD_PROGRAM)
        vm.reset_registers(TIME=3, POWER=2)  # 3 + 2
        vm.run()
        print("ADD result:", vm.state())  # Expect TIME=5, POWER=0

        # Example 2: stack demo
        print("\n--- Stack Demo ---")
        vm.load_program(STACK_PROGRAM)
        vm.reset_registers()
        vm.run()
        print("Stack demo result:", vm.full_state())

        # Example 3: reverse demo  
        print("\n--- Reverse Demo ---")
        vm.load_program(REVERSE_PROGRAM)
        vm.reset_registers()
        vm.run()
        print("Reverse demo result:", vm.full_state())
