# AssemblyViz - Group 1

## Team Members

- **Nikita Aleksii** - Scrum Master + Developer
- **Maria Fajardo** - Product Owner + Developer
- **Robby Votta** - Developer
- **Yurdanur Yolcu** - Developer

---

## What is it
A web-based visualizer for assembly language execution. Supports two architectures - a simple 8-bit educational CPU (HYMN) and the full 32-bit RISC-V base integer instruction set (RV32I). Both backends share the same design philosophy: parse, assemble, and simulate step by step so the frontend can visualize register and memory state at each instruction.
 
---
 
## Repository Structure
 
```
AssemblyViz/
├── backend/
│   ├── hymn/               # 8-bit HYMN CPU simulator
│   │   ├── tests/
│   │   ├── instructions.py
│   │   ├── parser.py
│   │   ├── machine.py
│   │   ├── executor.py
│   │   └── debugger.py
│   └── riscv/              # 32-bit RISC-V RV32I simulator
│       ├── tests/
│       ├── isa.py
│       ├── parser.py
│       ├── assembler.py
│       ├── decoder.py
│       ├── memory.py
│       ├── registers.py
│       └── simulation.py
└── frontend/               # Web interface
```
 
---
 
## Requirements
 
- Python 3.10 or higher
- No external dependencies - uses the standard library only
 
---
 
## Architectures
 
### HYMN
 
HYMN is a minimal 8-bit CPU designed for teaching. It has 3 registers (PC, AC, IR), 32 bytes of memory, and 8 instructions encoded in a single byte each. Programs are assembled from a simple mnemonic language and executed instruction by instruction.
 
See [`backend/hymn/README.md`](backend/hymn/README.md) for the full instruction set, architecture details, and usage examples.
 
### RISC-V (RV32I)
 
The RISC-V backend implements the full RV32I base integer instruction set. Source code goes through a two-pass parser that validates mnemonics, operands, and labels, then an assembler that encodes each instruction into a 32-bit machine word, and finally a step-through simulator that models memory, registers, and the fetch-decode-execute cycle.
 
See [`backend/riscv/README.md`](backend/riscv/README.md) for the full instruction set, pipeline, API reference, and usage examples.
 
---
 
## Design
 
Both backends follow the same layered structure:
 
- **Parser** — validates source text and builds a symbol table
- **Assembler / Executor** — encodes instructions into machine words
- **Simulator** — runs the fetch-decode-execute cycle step by step
- **Snapshot** — returns a JSON-serializable state dict after each step for the frontend to consume