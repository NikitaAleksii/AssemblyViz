from enum import IntEnum

# ——————————————————— Handle instruction opcodes ———————————————————


class InstructionOpcodes:
    OPreg = 0b0110011   # add, sub, sll, slt, sltu, xor, srl, sra, or, and
    OPimm = 0b0010011   # addi, slti, sltiu, ori, andi, slli, srli, srai
    LOAD = 0b0000011
    STORE = 0b0100011
    BRANCH = 0b1100011  # beq, bne, blt, bge, bltu, bgeu
    JAL = 0b1101111
    JALR = 0b1100111
    LUI = 0b0110111
    AUIPC = 0b0010111
    SYSTEM = 0b1110011  # ecall, ebreak

# ——————————————————— Handle encoding formats ———————————————————


class EncodingFormat:
    R = "R"  # register-register: add, sub, and, or
    I = "I"  # immediate: addi, load, jalr
    S = "S"  # stores: sb, sh, sw
    B = "B"  # branches: beq, blt
    U = "U"  # upper immediate: lui, auipc
    J = "J"  # jump: jal


# ——————————————————— Assign formats to each opcode ———————————————————
OPCODE_FORMATS = {
    InstructionOpcodes.OPreg: EncodingFormat.R,
    InstructionOpcodes.OPimm: EncodingFormat.I,
    InstructionOpcodes.LOAD: EncodingFormat.I,
    InstructionOpcodes.STORE: EncodingFormat.S,
    InstructionOpcodes.BRANCH: EncodingFormat.B,
    InstructionOpcodes.JAL: EncodingFormat.J,
    InstructionOpcodes.JALR: EncodingFormat.I,
    InstructionOpcodes.LUI: EncodingFormat.U,
    InstructionOpcodes.AUIPC: EncodingFormat.U,
    InstructionOpcodes.SYSTEM: EncodingFormat.I
}

# ——————————————————— Handle instruction mnemonics ———————————————————
# Assign mnemonics to instructions for better interpretability since it's hard to read binary code.
# A mnemonic looks either like (opcode, funct3) or like (opcode, funct3, funct7).
MNEMONICS = {
    # OPreg instructions
    (InstructionOpcodes.OPreg, 0b000, 0b0000000): "add",
    (InstructionOpcodes.OPreg, 0b000, 0b0100000): "sub",
    (InstructionOpcodes.OPreg, 0b001, 0b0000000): "sll",
    (InstructionOpcodes.OPreg, 0b010, 0b0000000): "slt",
    (InstructionOpcodes.OPreg, 0b011, 0b0000000): "sltu",
    (InstructionOpcodes.OPreg, 0b100, 0b0000000): "xor",
    (InstructionOpcodes.OPreg, 0b101, 0b0000000): "srl",
    (InstructionOpcodes.OPreg, 0b101, 0b0100000): "sra",
    (InstructionOpcodes.OPreg, 0b110, 0b0000000): "or",
    (InstructionOpcodes.OPreg, 0b111, 0b0000000): "and",

    # OPimm instructions
    (InstructionOpcodes.OPimm, 0b000): "addi",
    (InstructionOpcodes.OPimm, 0b010): "slti",
    (InstructionOpcodes.OPimm, 0b011): "sltiu",
    (InstructionOpcodes.OPimm, 0b100): "xori",
    (InstructionOpcodes.OPimm, 0b110): "ori",
    (InstructionOpcodes.OPimm, 0b111): "andi",

    (InstructionOpcodes.OPimm, 0b001, 0b0000000): "slli",
    (InstructionOpcodes.OPimm, 0b101, 0b0000000): "srli",
    (InstructionOpcodes.OPimm, 0b101, 0b0100000): "srai",

    # Load instructions
    (InstructionOpcodes.LOAD, 0b000): "lb",
    (InstructionOpcodes.LOAD, 0b001): "lh",
    (InstructionOpcodes.LOAD, 0b010): "lw",
    (InstructionOpcodes.LOAD, 0b100): "lbu",
    (InstructionOpcodes.LOAD, 0b101): "lhu",

    # Store instructions
    (InstructionOpcodes.STORE, 0b000): "sb",
    (InstructionOpcodes.STORE, 0b001): "sh",
    (InstructionOpcodes.STORE, 0b010): "sw",

    # Branch instructions
    (InstructionOpcodes.BRANCH, 0b000): "beq",
    (InstructionOpcodes.BRANCH, 0b001): "bne",
    (InstructionOpcodes.BRANCH, 0b100): "blt",
    (InstructionOpcodes.BRANCH, 0b101): "bge",
    (InstructionOpcodes.BRANCH, 0b110): "bltu",
    (InstructionOpcodes.BRANCH, 0b111): "bgeu",

    # Jump instructions
    (InstructionOpcodes.JAL, None): "jal",
    (InstructionOpcodes.JALR, 0b000): "jalr",

    # Upper immediate instructions
    (InstructionOpcodes.LUI, None): "lui",
    (InstructionOpcodes.AUIPC, None): "auipc",

    # System instructions
    (InstructionOpcodes.SYSTEM, 0b000): "ecall/ebreak"
}

# ——————————————————— Application Binary Interface ———————————————————
REGISTER_NAMES = [
    "zero",                 # hardwired zero
    "ra",                   # return address
    "sp",                   # stack pointer
    "gp",                   # global pointer
    "tp",                   # thread pointer
    "t0", "t1", "t2",       # temporaries
    "s0", "s1",             # saved registers
    "a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7",  # function arguments
    "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10", "s11",  # saved registers
    "t3", "t4", "t5", "t6"  # temporaries
]