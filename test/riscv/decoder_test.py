import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(_here))
sys.path.insert(0, os.path.join(_root, "backend"))
sys.modules.pop("riscv", None)

from riscv.decoder import DecodedInstruction
from riscv.isa import *
from riscv.assembler import *
from riscv.parser import *


def check(name, got, expected):
    status = "PASS" if got == expected else "FAIL"
    print(f"[{status}] {name}: got={got}, expected={expected}")


def decode_first(source):
    parser = Parser()
    parsed_lines = parser.parse(source)
    assembler = Assembler()
    words = assembler.assemble(parsed_lines, parser.symbol_table)
    return DecodedInstruction(words[0])


# --- OPreg: add x1, x2, x3 ---
d = decode_first("add x1, x2, x3")
check("add opcode",  d.opcode,  InstructionOpcodes.OPreg)
check("add rd",      d.rd,      1)
check("add rs1",     d.rs1,     2)
check("add rs2",     d.rs2,     3)
check("add funct3",  d.funct3,  0b000)
check("add funct7",  d.funct7,  0b0000000)
check("add isOPreg", d.isOPreg, True)

# --- OPimm: addi x1, x2, 10 ---
d = decode_first("addi x1, x2, 10")
check("addi opcode",  d.opcode,  InstructionOpcodes.OPimm)
check("addi isOPimm", d.isOPimm, True)
check("addi Iimm",    d.Iimm, 10)

# --- LOAD: lw x1, 4(x2) ---
d = decode_first("lw x1, 4(x2)")
check("lw opcode", d.opcode, InstructionOpcodes.LOAD)
check("lw isLoad", d.isLoad, True)
check("lw Iimm",   d.Iimm, 4)

# --- STORE: sw x1, 4(x2) ---
d = decode_first("sw x1, 4(x2)")
check("sw opcode",  d.opcode,  InstructionOpcodes.STORE)
check("sw isStore", d.isStore, True)
check("sw Simm",    d.Simm, 4)

# --- BRANCH: beq x1, x2, label ---
d = decode_first("beq x1, x2, label \n label:")
check("beq opcode",   d.opcode,   InstructionOpcodes.BRANCH)
check("beq isBranch", d.isBranch, True)

# --- JAL ---
d = decode_first("jal x1, label \n label:")
check("jal opcode", d.opcode, InstructionOpcodes.JAL)
check("jal isJal",  d.isJal,  True)

# --- LUI ---
d = decode_first("lui x1, 5")
check("lui opcode", d.opcode, InstructionOpcodes.LUI)
check("lui isLUI",  d.isLUI,  True)
check("lui Uimm",   d.Uimm, 5)

print("\nDone.")