# MicrowaveVM

A minimal Minsky-style virtual machine with just two registers and six instructions, proving Turing completeness through elegant simplicity.

## 🎯 Overview

MicrowaveVM is an educational virtual machine designed to demonstrate computational theory concepts while maintaining extreme simplicity. With only two registers (`TIME` and `POWER`) and six instructions, it can execute any computable algorithm, making it perfect for:

- **Computer Science Education**: Understanding computational minimalism
- **Compiler Development**: Building backends for ultra-constrained targets  
- **Algorithm Exploration**: Implementing classical algorithms with minimal resources
- **Theoretical Research**: Exploring computability and complexity theory

## 🏗️ Architecture

### Writable Registers
- **`TIME`**: General-purpose register (32-bit signed integer)
- **`POWER`**: General-purpose register (32-bit signed integer)

### Readonly Registers
- **`TEMP`**: Current temperature of the item in the microwave (°C, computed by thermal model)
- **`WEIGHT`**: Weight of the item in the microwave (grams, set at program initialization)

### Memory Model
- No addressable memory beyond registers
- Program counter (PC) for instruction sequencing
- Label-based control flow (computed at load time)
- Stack for temporary value storage (LIFO operations)

### Execution Model
- Sequential instruction execution
- Conditional branching based on zero-testing
- Deterministic state transitions
- Bounded by step limits (configurable, default: unlimited)
- **Thermal simulation**: TEMP register updated each instruction tick based on POWER and WEIGHT
- **Stack operations**: LIFO storage for temporary values

## 📝 Instruction Set Architecture (ISA)

| Instruction | Syntax | Description | Example |
|------------|--------|-------------|---------|
| **SET** | `SET R n` | Initialize register R to value n | `SET TIME 42` |
| **INC** | `INC R` | Increment register R by 1 | `INC POWER` |
| **DECJZ** | `DECJZ R label` | Decrement R; jump to label if zero | `DECJZ TIME loop_end` |
| **GOTO** | `GOTO label` | Unconditional jump to label | `GOTO main_loop` |
| **PRINT** | `PRINT` | Print current value of TIME register | `PRINT` |
| **PUSH** | `PUSH R` | Push register value onto stack | `PUSH TIME` |
| **POP** | `POP R` | Pop value from stack into register | `POP POWER` |
| **HALT** | `HALT` | Stop program execution | `HALT` |

### Labels
```assembly
label_name:     ; Define a jump target
    INC TIME    ; Instructions following the label
```

### Thermal Model

The MicrowaveVM includes a realistic thermal simulation that updates the `TEMP` register every instruction tick:

```
Temperature Change = (POWER × 0.1 - TEMP × 0.02) / √(WEIGHT/100)
```

**Model Characteristics:**
- **Heating Rate**: Proportional to POWER setting (0.1°C per power unit per tick)
- **Cooling Rate**: Natural heat loss proportional to current temperature (2% per tick)
- **Weight Effect**: Heavier items require more energy to heat (square root relationship)
- **Minimum Temperature**: Cannot go below 0°C (room temperature baseline)

**Example**: A 200g item with POWER=50 will heat at roughly 3.5°C per tick initially, slowing as temperature rises.

## 🚀 Quick Start

### Installation
```bash
git clone https://github.com/raulikeda/MicrowaveVM.git
cd MicrowaveVM
```

### Running Programs
```bash
# Run a program file
python3 main.py examples/factorial.mwasm

# Set item weight (default: 100g)
vm = MicrowaveVM()
vm.set_weight(250)  # 250 grams
vm.load_program(program)
vm.run()

# Run without arguments for demo
python3 main.py
```

### Your First Program
Create `hello.mwasm`:
```assembly
; Microwave heating simulation
    SET POWER 60        ; Set microwave to 60% power
    SET TIME 30         ; Heat for 30 seconds
    PRINT               ; Show initial time

heat_loop:
    DECJZ TIME done     ; Count down timer
    ; TEMP register automatically updates based on thermal model
    GOTO heat_loop      ; Continue heating

done:
    PRINT               ; Show final time (0)
    HALT                ; Microwave stops
```

Run it:
```bash
python3 main.py hello.mwasm
```

The program will show the temperature evolution as the item heats up!

## 🧮 Example Programs

The `examples/` directory contains implementations of classical algorithms:

- **`factorial.mwasm`** - Iterative factorial computation (5! = 120)
- **`exponentiation.mwasm`** - Fast exponentiation (3⁴ = 81) 
- **`gcd.mwasm`** - Greatest Common Divisor using subtraction
- **`collatz.mwasm`** - Collatz conjecture sequence
- **`prime.mwasm`** - Prime number testing
- **`popcorn.mwasm`** - Microwave simulation (thematic!)
- **`fibonacci.mwasm`** - Fibonacci sequence (incomplete)
- **`search.mwasm`** - Search in mathematical sequences

## 🔨 Building a Compiler for MicrowaveVM

### Target Architecture Constraints

When building a compiler targeting MicrowaveVM, consider these fundamental limitations:

#### 1. **Register Pressure**
- Only 2 writable registers available (TIME, POWER)
- 2 readonly registers for simulation (TEMP, WEIGHT)
- Stack available for temporary storage (PUSH/POP operations)
- No register spilling to memory beyond stack
- Consider using registers for multiple purposes within algorithms

#### 2. **No Arithmetic Operations**
- Only increment/decrement available
- Addition: Implement as repeated increment
- Subtraction: Implement using DECJZ loops  
- Multiplication: Nested addition loops
- Division: Repeated subtraction with quotient counting

#### 3. **Control Flow Limitations**
- Only conditional zero-testing available
- Comparison operations must be synthesized
- Loop constructs need careful zero-condition management

#### 4. **Data Representation**
- All values are signed integers
- No floating-point support
- Arrays/structures require encoding schemes or stack usage
- Boolean values: 0 (false) and non-zero (true)
- **Thermal simulation**: TEMP register provides realistic microwave heating
- **Weight modeling**: WEIGHT register affects heating characteristics

### Compilation Strategies

#### Variable Assignment
```c
// High-level: x = 5
// MicrowaveVM:
SET TIME 5      ; Assuming x maps to TIME register
```

#### Arithmetic Operations  
```c
// High-level: result = a + b
// MicrowaveVM (assuming a in TIME, b in POWER):
add_loop:
    DECJZ POWER add_done
    INC TIME
    GOTO add_loop
add_done:
    ; Result now in TIME, POWER = 0
```

#### Comparison Operations
```c  
// High-level: if (a == b)
// MicrowaveVM strategy - subtract until one reaches zero:
compare_loop:
    DECJZ TIME a_smaller    ; a was smaller
    DECJZ POWER b_smaller   ; b was smaller  
    GOTO compare_loop       ; Both still positive
a_smaller:
    ; Handle a < b case
b_smaller:  
    ; Handle b < a case
equal:
    ; Both reached zero simultaneously - they were equal
```

#### Loop Translation
```c
// High-level: for(i = 0; i < n; i++)
// MicrowaveVM (counter in POWER, n in TIME):
loop_start:
    DECJZ TIME loop_end     ; Exit if counter reaches target
    ; Loop body here
    INC POWER               ; Increment counter  
    GOTO loop_start
loop_end:
```

### Advanced Compiler Techniques

#### 1. **Register Allocation**
- Use graph coloring with only 2 colors (registers)
- Implement register coalescing for temporary values
- Consider register renaming for different algorithm phases

#### 2. **Instruction Scheduling**
- Minimize register conflicts
- Optimize for reduced instruction count
- Consider loop unrolling for small, fixed iterations

#### 3. **Code Generation Patterns**

**Pattern: Temporary Value Storage**
```assembly
; Modern approach: Use stack for temporary storage
    PUSH TIME           ; Save TIME value
    SET TIME 42         ; Use TIME for calculation
    ; ... do computation ...
    POP TIME            ; Restore original TIME value

; Legacy approach: Transfer between registers
save_time:
    DECJZ TIME restore_time
    INC POWER
    GOTO save_time
restore_time:
    ; TIME now 0, POWER has original TIME value
```

**Pattern: Value Restoration**  
```assembly
; Restore TIME from POWER
restore_from_power:
    DECJZ POWER restoration_done
    INC TIME
    GOTO restore_from_power
restoration_done:
    ; TIME restored, POWER now 0
```

**Pattern: Multiplication Implementation**
```assembly
; Multiply TIME by POWER (result in TIME)
multiply:
    SET TIME 0          ; Clear accumulator
mult_outer:
    DECJZ POWER mult_done
    ; Add original multiplicand POWER times
    ; (This requires saving the multiplicand first)
mult_done:
```

#### 4. **Optimization Opportunities**

- **Dead Code Elimination**: Remove unreachable labels
- **Constant Folding**: Pre-compute SET operations where possible
- **Loop Optimization**: Minimize register shuffling in tight loops
- **Peephole Optimization**: Combine adjacent INC/DECJZ patterns

#### 5. **Runtime Support**

Consider implementing runtime support routines for:
- **Division with remainder**
- **Modulo operations**  
- **Multi-precision arithmetic**
- **String/array encoding schemes**

### Error Handling in Compilation

Common compilation challenges:
- **Register exhaustion**: Need more than 2 simultaneous values
- **Infinite loops**: No automatic loop bounds checking
- **Overflow detection**: No built-in arithmetic overflow handling
- **Type checking**: All values are integers, no type safety

### Testing Your Compiler

1. **Unit Tests**: Verify individual operation translations
2. **Integration Tests**: Full program compilation and execution
3. **Performance Tests**: Measure instruction count for algorithms
4. **Correctness Tests**: Compare outputs with reference implementations

## 📚 Theoretical Background

### Turing Completeness

MicrowaveVM is Turing complete because it can simulate a Minsky machine:
- **Unbounded registers**: Can hold arbitrarily large integers
- **Conditional branching**: DECJZ provides conditional control flow
- **Looping**: GOTO enables arbitrary program flow

### Computational Complexity

- **Time Complexity**: Operations are linear in operand magnitude
- **Space Complexity**: O(1) register space, O(n) instruction space
- **Reduction**: Any algorithm can be reduced to this instruction set

## 🔧 VM Implementation Details

### Parser
- Two-pass assembly: labels collected first, then instructions
- Comment support: `;` and `#` prefixes
- Case-insensitive instruction names
- Flexible whitespace handling

### Runtime
- Step counting for infinite loop detection
- Configurable execution limits
- Error handling for undefined labels
- State inspection utilities
- **Thermal simulation**: Real-time temperature modeling
- **Stack operations**: LIFO temporary storage with overflow detection

### Debugging
- `PRINT` instruction for register inspection
- Step-by-step execution mode available
- Program counter tracking
- Register state logging
- **Thermal monitoring**: Track temperature changes during execution
- **Stack inspection**: View current stack contents and depth

## 🤝 Contributing

We welcome contributions! Areas of interest:

- **More example algorithms**
- **Compiler implementations** (for C, Python, etc.)
- **Performance optimizations**
- **Educational materials**
- **Debugging tools**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎓 Educational Use

Perfect for:
- **Compiler Construction Courses**: Minimal target for backend implementation
- **Theory of Computation**: Demonstrating Turing completeness
- **Algorithm Design**: Resource-constrained programming challenges
- **Computer Architecture**: Understanding minimal computational models
