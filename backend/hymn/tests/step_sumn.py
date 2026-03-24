#!/usr/bin/env python3
"""Step-by-step runner for the sumn HYMN assembly program.

Assembles sumn.s, then executes one instruction at a time, pausing for
Enter between each step so you can follow the registers and variables live.

Usage (from the repo root):
    python backend/hymn/tests/step_sumn.py
"""

import os
import sys

_BACKEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.normpath(_BACKEND))

from hymn.parser import Parser
from hymn.machine import MachineState

MNEMONICS = ["HALT", "JUMP", "JZER", "JPOS", "LOAD", "STOR", "ADD", "SUB"]


def main() -> None:
    sumn_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sumn.s')

    with open(sumn_path) as f:
        source = f.read()

    parser = Parser()
    words = parser.parse(source)

    if words is None:
        print("Assembly failed:")
        for err in parser.errors:
            print(f"  line {err.line_number}: {err.message}")
            print(f"    > {err.line_text}")
        sys.exit(1)

    machine = MachineState()
    machine.load_program(words)

    sym = parser.symbol_table  # uppercase keys, e.g. {'TOTAL': 8, 'COUNT': 9, ...}
    one_addr = sym.get('ONE')
    if one_addr is not None:
        machine.write_memory(one_addr, 1)

    # Reverse map: address -> label name (for decoding operands in the display)
    rev_sym = {v: k.lower() for k, v in sym.items()}

    # Data variables to watch on every line
    watch_keys = [k for k in ('TOTAL', 'COUNT') if k in sym]

    print("*" * 60)
    print("sumn — step-by-step execution")
    print("*" * 60)
    print()

    step_num = 0
    while not machine.halted:
        pc = machine.pc
        raw = machine.read_memory(pc)
        opcode, addr = MachineState.decode(raw)
        mnemonic = MNEMONICS[opcode]

        # Human-readable operand: use label name if one exists
        if mnemonic in ("LOAD",) and addr == MachineState.READ_ADDR:
            operand = "<READ>"
        elif mnemonic in ("STOR",) and addr == MachineState.WRITE_ADDR:
            operand = "<WRITE>"
        else:
            operand = rev_sym.get(addr, str(addr))

        # Named variable snapshot
        watch_str = "  ".join(
            f"{k.lower()}={machine.read_memory(sym[k])}" for k in watch_keys
        )

        print(
            f"step {step_num + 1:3d} | PC={pc:02d}  {mnemonic:<4} {operand:<8} | "
            f"AC={machine.ac:5d} | {watch_str}"
        )

        input("         >> execute next line: ")
        machine.step()
        step_num += 1

    # Final state after HALT
    print()
    print(f"HALTED after {step_num} steps")
    if 'TOTAL' in sym:
        print(f"Result: {machine.read_memory(sym['TOTAL'])}")


if __name__ == '__main__':
    main()
