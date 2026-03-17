# RISC-V Backend

Python backend for a RISC-V assembly visualizer. Handles assembling RV32I source code into 32-bit machine code words, which are then consumed by the frontend for visualization.

---

## RISC-V Implementation Structure

```
riscv/
├── tests/
│   ├── __init__.py
│   ├── assembler_test.py   # Unit tests for the assembler
│   ├── decoder_test.py     # Unit tests for the decoder
│   └── memory_test.py      # Unit tests for the memory
│   └── simulation_test.py  # Tests for the simulation
│   └── merge_sort.S        # Merge sort implemented in RISC-V and used for the simulation
├── __init__.py
├── isa.py                  # RV32I instruction set definitions (opcodes, formats, register names)
├── assembler.py            # Assembles RV32I source text - list of 32-bit machine code words
├── decoder.py              # Decodes machine code words - structured instruction objects
├── memory.py               # Byte-addressable memory model
├── registers.py            # x0–x31 register file
└── simulator.py            # Step-through execution engine
```

---

## Requirements

- Python 3.10 or higher
- No external dependencies — uses the standard library only

---

## Supported Instructions

The assembler currently supports the full **RV32I base integer instruction set**:

| Format | Instructions |
|--------|-------------|
| R-type | `add` `sub` `and` `or` `xor` `sll` `srl` `sra` `slt` `sltu` |
| I-type | `addi` `andi` `ori` `xori` `slti` `sltiu` `slli` `srli` `srai` |
| Load   | `lw` `lh` `lb` `lhu` `lbu` |
| Store  | `sw` `sh` `sb` |
| Branch | `beq` `bne` `blt` `bge` `bltu` `bgeu` |
| U-type | `lui` `auipc` |
| Jump   | `jal` `jalr` |
| System | `ecall` `ebreak` |

---

### Pseudo-instructions

| Pseudo | Expands to |
|--------|-----------|
| `li rd, imm` | `addi rd, x0, imm` (small) or `lui` + `addi` (large) |
| `la rd, symbol` | `lui rd, %hi(addr)` + `addi rd, rd, %lo(addr)` |
| `mv rd, rs` | `addi rd, rs, 0` |
| `j label` | `jal x0, offset` |
| `ret` | `jalr x0, ra, 0` |
| `nop` | `addi x0, x0, 0` |

---

## Syscall Convention (MARS/RISC-V)

Set `a7` to the syscall number before `ecall`:

| a7 | Operation |
|----|-----------|
| 1  | Print integer in `a0` — simulation continues |
| 4  | Print string at address in `a0` — simulation continues |
| 10 | Exit — simulation halts |

Any other syscall number also halts the simulation.

---

## Running the Simulator

Run the command from ./backend folder
``` 
cd backend/
```
```
python3 -m riscv.tests.simulation_test
```

### Simulation API

| Method | Description |
|--------|-------------|
| `Simulation(memory_depth=4096)` | Create a new simulation with `memory_depth` bytes of memory |
| `sim.load(source)` | Assemble source, write to memory, reset PC, set `sp` to top of memory |
| `sim.step()` | Execute one instruction and return a snapshot |
| `sim.reset()` | Clear memory and registers, reset PC |
| `sim.snapshot()` | Return current state: `PC`, `halted`, `registers`, `memory` |

### Snapshot format

```python
{
    "PC": 24,
    "halted": False,
    "registers": [
        {"index": 0, "names": "zero", "value": 0},
        {"index": 1, "names": "ra",   "value": 0},
        # ... x0–x31
    ],
    "memory": ["00000000...", ...]  # list of 32-bit binary strings
}
```

---

## Memory Layout

When a program with a `.data` section is loaded, the simulator lays it out as:

```
Address 0x0000  ┌─────────────────┐
                │   .text         │  instructions
                ├─────────────────┤
                │   .data         │  .word / .asciz values
                └─────────────────┘
Address depth   stack grows down ↓
```

The stack pointer (`sp`) is initialised to `memory_depth` on every `load()` call, so it starts at the top of memory and grows downward as functions push frames.