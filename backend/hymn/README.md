# HYMN

HYMN (Hypothetical Yet Minimalist Notation) is an 8-bit assembly language simulator. It models a CPU with 32 bytes of memory, three registers, and eight instructions.

## Architecture

### Registers

| Register | Role |
|---|---|
| **PC** (Program Counter) | Points to the next instruction in memory |
| **AC** (Accumulator) | General-purpose register where all math happens |
| **IR** (Instruction Register) | Holds the raw instruction word just fetched from memory |

### Instruction Encoding

Each instruction is a single 8-bit word:

```
[opcode (3 bits) | address (5 bits)]
 bits 7-5          bits 4-0
```

- 3-bit opcode: 8 possible instructions (0-7)
- 5-bit address: 32 possible memory addresses (0-31)

### Instruction Set

| Mnemonic | Opcode | Operand | Effect |
|---|---|---|---|
| `HALT` | `000` | none | Stop the machine |
| `JUMP` | `001` | address | PC = address |
| `JZER` | `010` | address | PC = address if AC == 0, else PC += 1 |
| `JPOS` | `011` | address | PC = address if AC > 0, else PC += 1 |
| `LOAD` | `100` | address | AC = memory[address]; PC += 1 |
| `STOR` | `101` | address | memory[address] = AC; PC += 1 |
| `ADD`  | `110` | address | AC = AC + memory[address]; PC += 1 |
| `SUB`  | `111` | address | AC = AC - memory[address]; PC += 1 |


## puseudo ops
In addition to the eight instructions listed above, the Hymn architecture supports two further “pseudo-ops”: READ and WRITE. As their names suggest, these
instructions read from and write to the I/O console, respectively.

## Modules

### `instructions.py`

Defines the `InstructionDef` dataclass and the `INSTRUCTIONS` / `INSTRUCTIONS_BY_OPCODE` registries. Each instruction's mnemonic, opcode, and operand types are declared here.

### `parser.py`

Two-pass assembler that converts HYMN assembly source text into a list of 8-bit machine words.

- **First pass**: builds a symbol table mapping labels (e.g. `LOOP:`) to memory addresses.
- **Second pass**: encodes each instruction, resolving label references via the symbol table.

Supports comments (`;`), labels on their own line or inline with instructions, and case-insensitive mnemonics. Parse errors are collected and accessible via the `errors` property.

### `machine.py`

The `MachineState` class simulating the HYMN CPU. Manages the three registers, 32 bytes of memory, and the fetch-decode-execute cycle. Provides `step()` for single-instruction execution, `run()` to execute until halt, and `snapshot()` for JSON-serializable state dumps.

### `executor.py`

High-level wrapper around `MachineState`. Provides `load()`, `step()`, `run()`, and `reset()` with a cleaner API that returns state snapshots after each action.

### `debugger.py`

Adds breakpoint support on top of `Executor`. Breakpoints are memory addresses; `run_until_break()` executes instructions until the PC hits a breakpoint or the machine halts. Also exposes `step()` for single-instruction stepping that ignores breakpoints.

## Usage

```python
from hymn.parser import Parser
from hymn.executor import Executor
from hymn.debugger import Debugger

# Assemble source code
parser = Parser()
words = parser.parse("""
    LOAD 10    ; AC = memory[10]
    ADD  11    ; AC = AC + memory[11]
    STOR 12    ; memory[12] = AC
    HALT
""")

# Run the program
ex = Executor()
ex.load(words)
result = ex.run()
print(result)  # {"pc": 3, "ac": ..., "ir": ..., "halted": True, "memory": [...]}

# Debug with breakpoints
ex.load(words)
dbg = Debugger(ex)
dbg.add_breakpoint(2)          # pause before STOR
state = dbg.run_until_break()  # stops at address 2
state = dbg.step()             # execute STOR
```

## Tests

Tests are in the `tests/` directory, one file per module:

- `test_instructions.py` - registry completeness, opcode ranges, immutability
- `test_parser.py` - tokenization, label resolution, encoding, full integration
- `test_machine.py` - all instructions, register behavior, memory, encode/decode
- `test_executor.py` - load, step, run, reset, state inspection
- `test_debugger.py` - breakpoint management, step, run_until_break

Run them with:

```bash
cd backend/hymn
pytest
```
