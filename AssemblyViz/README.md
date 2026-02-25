# AssemblyViz - Group 1

## Team Members

- **Nikita Aleksii** - Scrum Master + Developer
- **Maria Fajardo** - Product Owner + Developer
- **Robby Votta** - Developer
- **Yurdanur Yolcu** - Developer




***Full Tech Stack***

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


***About SimHYMN*** 

SimHYMN simulates a simple 8-instruction CPU and 32-byte memory designed for learning about how a CPU executes a program. The CPU contains three registers: IR (instruction register), PC (program counter), and AC (accumulator). The eight instructions are as follows.

code	
000	HALT	nothing happens
001	JUMP	PC := data
010	JZER	if AC = 0 then PC := data else PC := PC + 1
011	JPOS	if AC > 0 then PC := data else PC := PC + 1
100	LOAD	AC := M[data]; PC := PC + 1
101	STOR	AC := M[data]; PC := PC + 1
110	ADD	AC := AC + M[data]; PC := PC + 1
111	SUB	AC := AC - M[data]; PC := PC + 1
SimHYMN should run on any platform having Java 1.4. The program is free for your personal use, though you cannot distribute it to others.