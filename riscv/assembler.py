
def encode_R(funct7, rs2, rs1, funct3, rd, opcode) -> int:
    return (
        ((funct7 & 0b1111111) << 25) |
        ((rs2 & 0b11111) << 20) |
        ((rs1 & 0b11111) << 15) |
        ((funct3 & 0b111) << 12) |
        ((rd & 0b11111) << 7) |
        (opcode & 0b1111111)
    )


def encode_I(imm, rs1, funct3, rd, opcode) -> int:
    return (
        ((imm & 0b111111111111) << 20) |  # imm[11:0] - bits 31-20
        ((rs1 & 0b11111) << 15) |
        ((funct3 & 0b111) << 12) |
        ((rd & 0b11111) << 7) |
        (opcode & 0b1111111)
    )


def encode_S(imm, rs2, rs1, funct3, opcode) -> int:
    return (
        ((imm & 0b11111100000) << 20) |  # imm[11:5] - bits 31-25
        ((rs2 & 0b11111) << 20) |
        ((rs1 & 0b11111) << 15) |
        ((funct3 & 0b111) << 12) |
        ((imm & 0b00000011111) << 7) |
        (opcode & 0b1111111)
    )


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


def encode_U(imm, rd, opcode) -> int:
    return (
        ((imm & 0b11111111111111111111) << 12) |  # imm[19:0]
        ((rd & 0b11111) << 7) |
        (opcode & 0b1111111)
    )


def encode_J(imm, rd, opcode) -> int:
    return (
        (((imm >> 20) & 0b1) << 31) |  # imm[20]
        (((imm >> 1) & 0b1111111111) << 21) |  # imm[10:1]
        (((imm >> 11) & 0b1) << 20) |  # imm[11]
        (((imm >> 12) & 0b11111111) << 12) |  # imm[19:12]
        ((rd & 0b11111) << 7) |
        (opcode & 0b1111111)
    )


def assemble_line(instruction: str) -> int:
    instruction = instruction.replace(",", "").split()

    mnemonic = instruction[0].lower()

    return 0


def assemble(source: str) -> list[int]:
    words = []
    for instruction in source.strip().splitlines():
        instruction = instruction.split("#")[0].strip()

        if not instruction:
            continue

        words.append(assemble_line(instruction))

    return words
