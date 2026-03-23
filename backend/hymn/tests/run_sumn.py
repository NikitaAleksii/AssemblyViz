#!/usr/bin/env python3
"""Runner for the sumn HYMN assembly program.

Assembles sumn.s, patches the 'one' constant to 1, then runs the
program on the HYMN machine simulator.

Usage (from the repo root):
    python backend/hymn/tests/run_sumn.py
"""

import os
import sys

# Add backend/ to sys.path so hymn.* imports resolve correctly.
_BACKEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.normpath(_BACKEND))

from hymn.parser import Parser
from hymn.machine import MachineState


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

    # Patch 'one' to 1.  The parser encodes all data labels as HALT (byte 0);
    # the symbol table tells us which address to overwrite.
    one_addr = parser.symbol_table.get('ONE')
    if one_addr is not None:
        machine.write_memory(one_addr, 1)

    print("sumn — computing 1 + 2 + ... + n")
    print("Enter a positive integer n:")
    machine.run()   # prompts "? " for input, then prints the result


if __name__ == '__main__':
    main()
