# RISC-V Backend

Python backend for a RISC-V assembly visualizer. Handles assembling RV32I source code into 32-bit machine code words, which are then consumed by the frontend for visualization.

---

## Structure

```text
riscv/
├── tests/
│   ├── __init__.py
│   ├── assembler_test.py
│   ├── decoder_test.py
│   ├── memory_test.py
│   ├── merge_sort.S
│   ├── parser_test.py
│   └── simulation_test.py
├── __init__.py
├── isa.py
├── parser.py
├── assembler.py
├── decoder.py
├── memory.py
├── registers.py
└── simulation.py
```

---

## Module Descriptions

**isa.py** — Single source of truth for all ISA constants: opcodes, instruction type sets (`R_TYPE`, `I_TYPE`, etc.), register names, directives, and the mnemonic lookup table used by the decoder.

**parser.py** — Two-pass parser that takes raw assembly source and produces a list of `ParsedLine` objects. First pass builds the symbol table; second pass validates mnemonics, operands, and label references using regex.

**assembler.py** — Takes the `ParsedLine` list and symbol table from the parser and encodes each instruction into a 32-bit machine word. Handles pseudo-instruction expansion and PC-relative offset calculation.

**decoder.py** — Takes a 32-bit machine word and splits it into its constituent fields (opcode, rd, rs1, rs2, funct3, funct7, immediate). Used by the simulator to execute each fetched instruction.

**memory.py** — Byte-addressable memory model. Supports partial writes via a 4-bit byte mask, enabling byte and halfword stores. All addresses must be word-aligned.

**registers.py** — Models the 32 RISC-V general-purpose registers. x0 is hardwired to zero — writes are ignored and reads always return 0.

**simulation.py** — Ties everything together. Loads and assembles source, then runs the fetch-decode-execute cycle one instruction at a time via `step()`.

---

## Requirements

- Python 3.10 or higher
- No external dependencies — uses the standard library only

---

## Supported Instructions

The assembler supports the full **RV32I base integer instruction set**:

| Format | Instructions |
| --- | --- |
| R-type | `add` `sub` `and` `or` `xor` `sll` `srl` `sra` `slt` `sltu` |
| I-type | `addi` `andi` `ori` `xori` `slti` `sltiu` `slli` `srli` `srai` |
| Load | `lw` `lh` `lb` `lhu` `lbu` |
| Store | `sw` `sh` `sb` |
| Branch | `beq` `bne` `blt` `bge` `bltu` `bgeu` |
| U-type | `lui` `auipc` |
| Jump | `jal` `jalr` |
| System | `ecall` `ebreak` |

---

### Pseudo-instructions

| Pseudo | Expands to |
| --- | --- |
| `li rd, imm` | `addi rd, x0, imm` (small) or `lui` + `addi` (large) |
| `la rd, symbol` | `lui rd, %hi(addr)` + `addi rd, rd, %lo(addr)` |
| `mv rd, rs` | `addi rd, rs, 0` |
| `j label` | `jal x0, offset` |
| `ret` | `jalr x0, ra, 0` |
| `nop` | `addi x0, x0, 0` |

---

## Syscall Convention

Set `a7` to the syscall number before `ecall`:

| a7 | Operation |
| --- | --- |
| 1 | Print integer in `a0` — simulation continues |
| 4 | Print string at address in `a0` — simulation continues |
| 10 | Exit — simulation halts |

Any other syscall number also halts the simulation.

---

## Running the Tests

From the `backend/` directory:

```bash
python3 -m riscv.tests.simulation_test
```

Or run all tests with pytest:

```bash
cd backend/
pytest riscv/tests/
```

---

## Simulation API

| Method | Description |
| --- | --- |
| `Simulation(memory_depth=4096)` | Create a new simulation with `memory_depth` bytes of memory |
| `sim.load(source)` | Parse and assemble source, write to memory, reset PC, set `sp` to top of memory |
| `sim.step()` | Execute one instruction and return a snapshot |
| `sim.reset()` | Clear memory and registers, reset PC |
| `sim.snapshot()` | Return current state: `PC`, `halted`, `registers`, `memory` |
| `sim.read_label(label, count=1)` | Read `count` words from the address of `label` — returns `list[int]` or `None` if label not found |

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

```text
Address 0x0000  ┌─────────────────┐
                │   .text         │  instructions
                ├─────────────────┤
                │   .data         │  .word / .asciz values
                └─────────────────┘
Address depth   stack grows down ↓
```

The stack pointer (`sp`) is initialised to `memory_depth` on every `load()` call, so it starts at the top of memory and grows downward as functions push frames.
