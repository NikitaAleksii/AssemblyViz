# AssemblyViz - Group 1

## Team Members

- **Nikita Aleksii** - Scrum Master + Developer
- **Maria Fajardo** - Product Owner + Developer
- **Robby Votta** - Developer
- **Yurdanur Yolcu** - Developer

***stack***

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
│   ├── riscv/              # Add later, same structure
│   │   ├── __init__.py
│   │   ├── machine.py
│   │   ├── instructions.py
│   │   ├── parser.py
│   │   └── executor.py
│   ├── shared/
│   │   ├── __init__.py
│   │   └── types.py        # Base classes/interfaces shared across ISAs
│   └── tests/
│       ├── test_hymn_parser.py
│       ├── test_hymn_executor.py
│       └── ...