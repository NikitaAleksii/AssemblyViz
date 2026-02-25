from riscv.isa import *

pc = 0
labels = {}


def int_or_label(label) -> int:
    if label in labels:
        return labels[label] - pc

    return int(label, 0)

# Register Instruction
# funct7(7b) | rs2(5b) | rs1(5b) | funct3(3b) | opcode(7b)
def encode_R(funct7, rs2, rs1, funct3, rd, opcode) -> int:
    return (
        ((funct7 & 0b1111111) << 25) |
        ((rs2 & 0b11111) << 20) |
        ((rs1 & 0b11111) << 15) |
        ((funct3 & 0b111) << 12) |
        ((rd & 0b11111) << 7) |
        (opcode & 0b1111111)
    )

# Immediate Instruction
# imm(12b) | rs1(5b) | funct3(3b) | rd(5b) | opcode(7b)
def encode_I(imm, rs1, funct3, rd, opcode) -> int:
    return (
        ((imm & 0b111111111111) << 20) |  # imm[11:0] - bits 31-20
        ((rs1 & 0b11111) << 15) |
        ((funct3 & 0b111) << 12) |
        ((rd & 0b11111) << 7) |
        (opcode & 0b1111111)
    )

# Store Instruction
# imm[11:5] | rs2(5b) | rs1(5b) | funct3(3b) | imm[4:0] | opcode(7b)
def encode_S(imm, rs2, rs1, funct3, opcode) -> int:
    return (
        (((imm >> 5) & 0b1111111) << 25) |  # imm[11:5] - bits 31-25
        ((rs2 & 0b11111) << 20) |
        ((rs1 & 0b11111) << 15) |
        ((funct3 & 0b111) << 12) |
        ((imm & 0b00000011111) << 7) |
        (opcode & 0b1111111)
    )

# Branch Instruction
# imm[12] | imm[10:5] | rs2(5b) | rs1(5b) | funct3(3b) | imm[4:1] | imm[11] | opcode(7b)
def encode_B(imm, rs2, rs1, funct3, opcode) -> int:
    return (
        (((imm >> 12) & 0b1) << 31) |  # imm[12]
        (((imm >> 5) & 0b111111) << 25) |  # imm[10:5]
        ((rs2 & 0b11111) << 20) |
        ((rs1 & 0b11111) << 15) |
        ((funct3 & 0b111) << 12) |
        (((imm >> 1) & 0b1111) << 8) |  # imm[4:1]
        (((imm >> 11) & 0b1) << 7) |  # imm[11]
        (opcode & 0b1111111)
    )

# Upper Immediate Instruction
# imm[31:12] | rd(5b) | opcode(7b)
def encode_U(imm, rd, opcode) -> int:
    return (
        ((imm & 0b11111111111111111111) << 12) |  # imm[19:0]
        ((rd & 0b11111) << 7) |
        (opcode & 0b1111111)
    )

# Unconditional Jump
# imm[20] | imm[10:1] | imm[11] | imm[19:12] | rd(5b) | opcode(7b)
def encode_J(imm, rd, opcode) -> int:
    return (
        (((imm >> 20) & 0b1) << 31) |  # imm[20]
        (((imm >> 1) & 0b1111111111) << 21) |  # imm[10:1]
        (((imm >> 11) & 0b1) << 20) |  # imm[11]
        (((imm >> 12) & 0b11111111) << 12) |  # imm[19:12]
        ((rd & 0b11111) << 7) |
        (opcode & 0b1111111)
    )


ABI = {name: i for i, name in enumerate(REGISTER_NAMES)}


def reg(name: str) -> int:
    name = name.strip().lower()
    if name in ABI:
        return ABI[name]
    return int(name[1:])


def assemble_line(instruction: str) -> int:
    parts = instruction.replace(",", "").split()
    mnemonic = parts[0].lower()

    # ——————————————————— R-Type ———————————————————
    if mnemonic == "add":
        return encode_R(0b0000000, reg(parts[3]), reg(parts[2]), 0b000, reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "sub":
        return encode_R(0b0100000, reg(parts[3]), reg(parts[2]), 0b000, reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "sll":
        return encode_R(0b0000000, reg(parts[3]), reg(parts[2]), 0b001, reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "slt":
        return encode_R(0b0000000, reg(parts[3]), reg(parts[2]), 0b010, reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "sltu":
        return encode_R(0b0000000, reg(parts[3]), reg(parts[2]), 0b011, reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "xor":
        return encode_R(0b0000000, reg(parts[3]), reg(parts[2]), 0b100, reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "srl":
        return encode_R(0b0000000, reg(parts[3]), reg(parts[2]), 0b101, reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "sra":
        return encode_R(0b0100000, reg(parts[3]), reg(parts[2]), 0b101, reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "or":
        return encode_R(0b0000000, reg(parts[3]), reg(parts[2]), 0b110, reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "and":
        return encode_R(0b0000000, reg(parts[3]), reg(parts[2]), 0b111, reg(parts[1]), InstructionOpcodes.OPreg)

    # ——————————————————— I-Type ALU ———————————————————
    elif mnemonic == "addi":
        return encode_I(int(parts[3]), reg(parts[2]), 0b000, reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "slti":
        return encode_I(int(parts[3]), reg(parts[2]), 0b010, reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "sltiu":
        return encode_I(int(parts[3]), reg(parts[2]), 0b011, reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "xori":
        return encode_I(int(parts[3]), reg(parts[2]), 0b100, reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "ori":
        return encode_I(int(parts[3]), reg(parts[2]), 0b110, reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "andi":
        return encode_I(int(parts[3]), reg(parts[2]), 0b111, reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "slli":
        return encode_I(int(parts[3]) & 0b11111, reg(parts[2]), 0b001, reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "srli":
        return encode_I(int(parts[3]) & 0b11111, reg(parts[2]), 0b101, reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "srai":
        # srai encodes funct7=0100000 in the upper 7 bits of the immediate
        return encode_I((0b0100000 << 5) | (int(parts[3]) & 0b11111), reg(parts[2]), 0b101, reg(parts[1]), InstructionOpcodes.OPimm)

    # ——————————————————— I-Type LOAD ———————————————————
    elif mnemonic in ["lw", "lh", "lb", "lbu", "lhu"]:
        offset, rs1 = parts[2].split("(")
        rs1 = rs1.strip(")")
        funct3 = {"lb": 0b000, "lh": 0b001, "lw": 0b010,
                  "lbu": 0b100, "lhu": 0b101}[mnemonic]
        return encode_I(int(offset, 0), reg(rs1), funct3, reg(parts[1]), InstructionOpcodes.LOAD)

    # ——————————————————— I-Type JALR ———————————————————
    elif mnemonic == "jalr":
        return encode_I(int(parts[3]), reg(parts[2]), 0b000, reg(parts[1]), InstructionOpcodes.JALR)

    # ——————————————————— I-Type System ———————————————————
    elif mnemonic == "ecall":
        return encode_I(0, 0, 0b000, 0, InstructionOpcodes.SYSTEM)
    elif mnemonic == "ebreak":
        return encode_I(1, 0, 0b000, 0, InstructionOpcodes.SYSTEM)

    # ——————————————————— S-Type Store ———————————————————
    elif mnemonic in ["sw", "sh", "sb"]:
        offset, rs1 = parts[2].split("(")
        rs1 = rs1.strip(")")
        funct3 = {"sw": 0b010, "sh": 0b001, "sb": 0b000}[mnemonic]
        return encode_S(int(offset, 0), reg(parts[1]), reg(rs1), funct3, InstructionOpcodes.STORE)

    # ——————————————————— B-Type Branch ———————————————————
    elif mnemonic in ["beq", "bne", "blt", "bge", "bltu", "bgeu"]:
        funct3 = {"beq": 0b000, "bne": 0b001, "blt": 0b100,
                  "bge": 0b101, "bltu": 0b110, "bgeu": 0b111}[mnemonic]
        return encode_B(int_or_label(parts[3]), reg(parts[2]), reg(parts[1]), funct3, InstructionOpcodes.BRANCH)

    # ——————————————————— U-Type Branch ———————————————————
    elif mnemonic == "lui":
        return encode_U(int(parts[2]), reg(parts[1]), InstructionOpcodes.LUI)
    elif mnemonic == "auipc":
        return encode_U(int(parts[2]), reg(parts[1]), InstructionOpcodes.AUIPC)

    # ——————————————————— J-Type Branch ———————————————————
    elif mnemonic == "jal":
        return encode_J(int_or_label(parts[2]), reg(parts[1]), InstructionOpcodes.JAL)

    raise ValueError(f"Unknown Instruction: {mnemonic}")


def assemble(source: str) -> list[int]:
    global pc
    global labels

    words = []

    lines = source.strip().splitlines()
    instructions = [line.split("#")[0].strip() for line in lines]

    for instruction in instructions:
        if not instruction or instruction.startswith("#"):
            continue
        if ":" in instruction:
            labels[instruction.split(":")[0]] = pc
            continue
        pc += 4

    pc = 0

    for instruction in instructions:
        if not instruction or instruction.startswith("#"):
            continue
        if ":" in instruction:
            continue
        words.append(assemble_line(instruction))

        pc += 4

    return words


def main():
    source = "add x1, x2, x3 \n add x5, x5, x6 \n label: \n add x5, x5, x6 \n jal x1 label"
    words = assemble(source)
    print(words)
    print(labels)


if __name__ == "__main__":
    main()
