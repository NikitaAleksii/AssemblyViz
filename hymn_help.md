HYMN Backend — Full Technical Report

  Architecture Overview
  
  The backend/hymn folder is a complete simulation stack for the HYMN ISA (Instruction Set Architecture) — a toy CPU with 8 instructions, 3
  registers, and 32 bytes of memory. It is written in Python and follows a clean layered architecture:
                                                                                                                                                  
  Parser  →  Executor  →  MachineState
                    ↑
                Debugger (optional layer)                                                                                                         
  
  ---                                                                                                                                             
  Files & Their Roles
                                                                                                                                                  
  instructions.py
  - Defines an InstructionDef frozen dataclass with mnemonic, opcode, and operands
  - Builds two registries: INSTRUCTIONS (mnemonic → def) and INSTRUCTIONS_BY_OPCODE (opcode → def)
  - Uses a _def() helper to register all 8 instructions simultaneously in both dicts
  - OperandType.ADDRESS is the only operand type (5-bit, 0–31)
                                                                                                                                                  
  machine.py — The CPU simulator (MachineState)
  - Registers: PC (program counter), AC (accumulator), IR (instruction register)
  - Memory: 32 bytes (addresses 0–31)
  - Memory-mapped I/O: address 30 = keyboard input (READ), address 31 = console output (WRITE)
  - Implements step() (fetch-decode-execute), run() (loops until HALT), snapshot() (JSON dict)
  - AC is a plain Python int — no 8-bit wrapping
  - encode(opcode, addr) / decode(word) as static methods for 3-bit opcode + 5-bit address
                                                                                                                                                  
  parser.py — Two-pass assembler (Parser)
  - Pass 1: scans for label definitions (e.g. LOOP:) and maps them to addresses → symbol table
  - Pass 2: encodes each instruction to an 8-bit word, resolves label operands
  - Handles pseudo-ops: READ → LOAD 30, WRITE → STOR 31
  - Accumulates all errors instead of failing on the first one; returns None if any errors exist
  - Tokenizer strips comments (;), normalizes to uppercase, handles inline labels
                                                                                                                                                  
  executor.py — High-level API wrapper (Executor)
  - Wraps MachineState via composition (not inheritance)
  - load(words, origin=0) → resets state then loads program
  - step() and run() both return a snapshot() dict
  - Designed for frontend consumption (JSON-serializable output)
                                                                                                                                                  
  debugger.py — Breakpoint control layer (Debugger)
  - Wraps Executor; manages a set of breakpoint addresses
  - run_until_break() — steps until PC hits a breakpoint OR machine halts
  - Stops before executing the breakpoint instruction (PC == breakpoint address when paused)
  - step() ignores breakpoints (single-instruction stepping)
                                                                                                                                                  
  ---                                                                                                                                             
  The 8 HYMN Instructions
                                                                                                                                                  
  ┌───────────┬────────┬───────────────────────────┐
  │ Mnemonic  │ Opcode │          Effect           │
  ├───────────┼────────┼───────────────────────────┤
  │ HALT      │ 000    │ Stop execution            │
  ├───────────┼────────┼───────────────────────────┤
  │ JUMP addr │ 001    │ PC = addr (unconditional) │
  ├───────────┼────────┼───────────────────────────┤
  │ JZER addr │ 010    │ PC = addr if AC == 0      │
  ├───────────┼────────┼───────────────────────────┤
  │ JPOS addr │ 011    │ PC = addr if AC > 0       │
  ├───────────┼────────┼───────────────────────────┤
  │ LOAD addr │ 100    │ AC = memory[addr]         │
  ├───────────┼────────┼───────────────────────────┤
  │ STOR addr │ 101    │ memory[addr] = AC         │
  ├───────────┼────────┼───────────────────────────┤
  │ ADD addr  │ 110    │ AC = AC + memory[addr]    │
  ├───────────┼────────┼───────────────────────────┤
  │ SUB addr  │ 111    │ AC = AC - memory[addr]    │
  └───────────┴────────┴───────────────────────────┘
  
  Pseudo-ops: READ → LOAD 30, WRITE → STOR 31
                  
  Encoding: [ooo | aaaaa] — 3-bit opcode, 5-bit address = 8-bit word
  
  ---                                                                                                                                             
  Tests
       
  ┌──────────────────────┬─────────┬────────────────────────────────────────────────────────────────────────────────┐
  │         File         │ Classes │                                 What's tested                                  │
  ├──────────────────────┼─────────┼────────────────────────────────────────────────────────────────────────────────┤
  │ test_instructions.py │ 5       │ Registry completeness, opcodes 0–7, immutability                               │
  ├──────────────────────┼─────────┼────────────────────────────────────────────────────────────────────────────────┤
  │ test_parser.py       │ 8       │ Tokenization, two-pass logic, label resolution, error accumulation, pseudo-ops │
  ├──────────────────────┼─────────┼────────────────────────────────────────────────────────────────────────────────┤
  │ test_machine.py      │ 14      │ All 8 instructions, memory-mapped I/O, encode/decode, PC overflow, snapshot    │
  ├──────────────────────┼─────────┼────────────────────────────────────────────────────────────────────────────────┤
  │ test_executor.py     │ 6       │ load/reset/step/run lifecycle, JSON state output                               │
  ├──────────────────────┼─────────┼────────────────────────────────────────────────────────────────────────────────┤
  │ test_debugger.py     │ 4       │ Breakpoint add/remove/clear, run_until_break stops before breakpoint           │
  └──────────────────────┴─────────┴────────────────────────────────────────────────────────────────────────────────┘
                  
  Demo programs: sumn.s (sum 1 to n), run_sumn.py (auto-run), step_sumn.py (interactive stepper)
                  
  ---                                                                                                                                             
  Key Design Decisions
                      
  - Composition over inheritance throughout (Debugger wraps Executor wraps MachineState)
  - No AC overflow wrapping — AC is unbounded Python int by design
  - Error accumulation in parser — all errors reported at once, not first-fail
  - Snapshot returns copies — memory list is a copy so callers can't corrupt state
  - Breakpoint stops before execution — PC points to breakpoint address, instruction not yet run
  - Pseudo-ops outside the instruction registry — handled as special cases in _encode_line()
                                                                                                                                                  
  ---                                                                                                                                             
  ---                                                                                                                                             
  20 Technical Interview Questions
                                  
  Instructions / ISA Design
                                                                                                                                                  
  1. The HYMN ISA uses 3-bit opcodes and 5-bit addresses packed into an 8-bit word. What are the hard limits this imposes — how many distinct
  instructions can exist, and what is the maximum addressable memory?
  2. Why does HYMN have two conditional jump instructions (JZER, JPOS) instead of one general-purpose branch? How would you implement a "jump if
  negative" behavior using only the existing instruction set?
  3. Memory-mapped I/O maps address 30 to keyboard input and address 31 to console output. What are the trade-offs of this approach compared to
  having dedicated I/O instructions?
                  
  Parser / Assembly
                  
  4. Walk me through what happens when the parser encounters a forward reference — a label used before it is defined. Why does a single-pass
  approach fail here, and how does the two-pass design solve it?
  5. The parser normalizes all tokens to uppercase but still stores labels case-sensitively in the symbol table. Could this cause a bug? Describe 
  a scenario where it would.
  6. The parser returns None instead of a partial result when any errors are found. What is the rationale for this? What would be the risk of
  returning a partially-assembled program?
  7. Pseudo-ops READ and WRITE are not in the INSTRUCTIONS registry — they are handled as special cases in _encode_line(). Why not just add them
  to the registry like the real instructions?
                  
  MachineState / CPU Simulation
                  
  8. In machine.py, the accumulator (AC) is a plain Python int with no wrapping at 8 bits. A sequence of ADD instructions can produce a value like
   400 or 1000. What real CPU behavior does this diverge from, and what impact does it have on programs like sumn.s?
  9. Trace through the fetch-decode-execute cycle for the instruction ADD 5 stored at address 2 in memory. What happens to IR, PC, and AC at each 
  phase?
  10. The JPOS instruction jumps only when AC > 0, not >= 0. Write a sequence of HYMN instructions (you can use pseudocode) that branches when AC 
  >= 0.
  11. When PC exceeds address 31, step() raises an error rather than wrapping around or silently halting. What class of bug does this catch, and
  why is an error better than wrapping?
                  
  Executor & Debugger
                  
  12. Executor.load() calls machine.reset() before loading the program. Why is this order important? What could go wrong if load_program() was
  called before reset()?
  13. Debugger.run_until_break() stops before executing the instruction at the breakpoint address. What is the practical consequence of this for a
   user debugging a program? Why is this behavior preferable to stopping after?
  14. The Debugger wraps an Executor, which wraps a MachineState. This is three layers of composition. What would the downside be if Debugger
  directly extended MachineState via inheritance instead?
                  
  Testing
                  
  15. test_machine.py tests that snapshot() returns a copy of the memory list, not a reference. Why is this important? Write a one-line test that 
  would fail if snapshot returned the live reference.
  16. Several tests inject a custom input_fn and output_fn into MachineState. What software design principle does this demonstrate, and why does
  it make the I/O tests reliable without needing real console interaction?
  17. The parser tests include tests for error accumulation — verifying that multiple errors in one source file are all reported, not just the
  first. From a user experience perspective, why does this matter?
                  
  Architecture & Trade-offs
                  
  18. The snapshot() dict is described as "JSON-serializable." Why is this property specifically useful given the context of a backend/frontend
  split? What would break if snapshot() returned Python objects like sets or custom class instances?
  19. Suppose you wanted to add a CALL addr instruction (subroutine call, pushes return address). HYMN has no stack and no spare opcode bits with 
  the current 3-bit opcode scheme. What would you need to change at the ISA, machine, and parser levels to support this?
  20. The InstructionDef dataclass is frozen (frozen=True). If a teammate wanted to add a runtime "usage counter" field to track how many times
  each instruction was executed, why would frozen be a problem, and what is the proper way to implement instruction execution tracking without
  modifying InstructionDef?
