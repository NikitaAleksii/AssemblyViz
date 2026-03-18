# AssemblyViz - Group 1

## Team Members

- **Nikita Aleksii** - Scrum Master + Developer
- **Maria Fajardo** - Product Owner + Developer
- **Robby Votta** - Developer
- **Yurdanur Yolcu** - Developer

## Project Structure

```
├── frontend/           # React + TypeScript
│   └── ...
├── backend/
│   ├── hymn/
│   │   ├── __init__.py
│   │   ├── machine.py      # MachineState class (registers, memory, PC, flags)
│   │   ├── instructions.py # Instruction set definitions
│   │   ├── parser.py       # Assembly text → instruction objects
│   │   ├── executor.py     # step() function, executes one instruction
│   │   └── debugger.py     # Breakpoints, run controls
│   ├── riscv/
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── assembler_test.py
│   │   │   ├── decoder_test.py
│   │   │   ├── memory_test.py
│   │   │   ├── simulation_test.py
│   │   │   └── merge_sort.S        # Merge sort used for simulation tests
│   │   ├── __init__.py
│   │   ├── isa.py          # Opcodes, encoding formats, mnemonics, register names
│   │   ├── assembler.py    # Assembles RV32I source text into 32-bit machine code words
│   │   ├── decoder.py      # Decodes 32-bit machine code words into structured objects
│   │   ├── memory.py       # Word-addressable memory model with byte-mask writes
│   │   ├── registers.py    # x0–x31 register file
│   │   └── simulation.py   # Step-through execution engine
```