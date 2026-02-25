from riscv.decoder import DecodedInstruction
from riscv.isa import *
from riscv.assembler import *


def test(name, got, expected):
    status = "PASS" if got == expected else "FAIL"
    print(f"[{status}] {name}: got={got}, expected={expected}")


def decode_first(source):
    return DecodedInstruction(assemble(source)[0])


# --- OPreg: add x1, x2, x3 ---
d = decode_first("add x1, x2, x3")
test("add opcode",  d.opcode,  InstructionOpcodes.OPreg)
test("add rd",      d.rd,      1)
test("add rs1",     d.rs1,     2)
test("add rs2",     d.rs2,     3)
test("add funct3",  d.funct3,  0b000)
test("add funct7",  d.funct7,  0b0000000)
test("add isOPreg", d.isOPreg, True)

# --- OPimm: addi x1, x2, 10 ---
d = decode_first("addi x1, x2, 10")
test("addi opcode",  d.opcode,  InstructionOpcodes.OPimm)
test("addi isOPimm", d.isOPimm, True)
test("addi Iimm",    int(d.Iimm, 2) & 0xFFF, 10)

# --- LOAD: lw x1, 4(x2) ---
d = decode_first("lw x1, 4(x2)")
test("lw opcode", d.opcode, InstructionOpcodes.LOAD)
test("lw isLoad", d.isLoad, True)
test("lw Iimm",   int(d.Iimm, 2) & 0xFFF, 4)

# --- STORE: sw x1, 4(x2) ---
d = decode_first("sw x1, 4(x2)")
test("sw opcode",  d.opcode,  InstructionOpcodes.STORE)
test("sw isStore", d.isStore, True)
test("sw Simm",    int(d.Simm, 2) & 0xFFF, 4)

# --- BRANCH: beq x1, x2, label ---
d = decode_first("beq x1, x2, label \n label:")
test("beq opcode",   d.opcode,   InstructionOpcodes.BRANCH)
test("beq isBranch", d.isBranch, True)

# --- JAL ---
d = decode_first("jal x1, label \n label:")
test("jal opcode", d.opcode, InstructionOpcodes.JAL)
test("jal isJal",  d.isJal,  True)

# --- LUI ---
d = decode_first("lui x1, 5")
test("lui opcode", d.opcode, InstructionOpcodes.LUI)
test("lui isLUI",  d.isLUI,  True)
test("lui Uimm",   int(d.Uimm, 2) >> 12, 5)

print("\nDone.")