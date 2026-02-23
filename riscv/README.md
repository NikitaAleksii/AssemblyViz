# RISC-V Backend

Python backend for a RISC-V assembly visualizer. Handles assembling RV32I source code into 32-bit machine code words, which are then consumed by the frontend for visualization.

> **Status:** In progress — assembler and ISA definitions are implemented. Decoder, memory, registers, and simulator are planned.

---

## Project Structure

```
riscv/
├── tests/
│   ├── __init__.py
│   └── assembler_test.py   # Unit tests for the assembler
├── __init__.py
├── isa.py                  # RV32I instruction set definitions (opcodes, formats, register names)
├── assembler.py            # Assembles RV32I source text → list of 32-bit machine code words
├── decoder.py              # (planned) Decodes machine code words → structured instruction objects
├── memory.py               # (planned) Byte-addressable memory model
├── registers.py            # (planned) x0–x31 register file
└── simulator.py            # (planned) Step-through execution engine
```

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

## Requirements

- Python 3.10 or higher
- No external dependencies — uses the standard library only

---

## Running the Assembler

You can use the assembler directly in a Python script:

```python
from riscv.assembler import assemble

source = """
    addi x1, x0, 5     # x1 = 5
    addi x2, x0, 10    # x2 = 10
    add  x3, x1, x2    # x3 = x1 + x2
"""

words = assemble(source)

for word in words:
    print(f"{word:032b}")   # print as 32-bit binary
    print(f"{word:#010x}")  # print as hex
```

Or run it standalone from the project root:

```bash
cd ~/Desktop/AssemblyViz
python3 -m riscv.assembler
```

### Assembly Syntax

```asm
# Registers: x0–x31 or ABI names (zero, ra, sp, a0 … t6)
add  x1, x2, x3          # rd, rs1, rs2
addi x1, x2, 10          # rd, rs1, immediate (decimal)
addi x1, x2, 0xFF        # rd, rs1, immediate (hex also works)
lw   x1, 8(x2)           # rd, offset(rs1)
sw   x2, 8(x1)           # rs2, offset(rs1)
beq  x1, x2, 4           # rs1, rs2, offset

# Comments use #
# Blank lines are ignored
```

---

## Running the Tests

From the **project root** (`AssemblyViz/`), run:

```bash
python3 -m riscv.tests.assembler_test
```

You should see output like:

```
test_add (__main__.TestRType.test_add) ... ok
test_sub (__main__.TestRType.test_sub) ... ok
test_and (__main__.TestRType.test_and) ... ok
...
----------------------------------------------------------------------
Ran 42 tests in 0.003s

OK
```