from riscv.isa import *

"""
Implements a RISC-V RV32I assembler.

Takes a string of assembly source code and converts it into a list of
32-bit machine code words that can be loaded into the memory model.

Supports the full RV32I base integer instruction set:
- R-type:  add, sub, and, or, xor, sll, srl, sra, slt, sltu
- I-type:  addi, andi, ori, xori, slti, sltiu, slli, srli, srai
- Load:    lw, lh, lb, lhu, lbu
- Store:   sw, sh, sb
- Branch:  beq, bne, blt, bge, bltu, bgeu
- U-type:  lui, auipc
- Jump:    jal, jalr
- System:  ecall, ebreak

Syntax rules:
- Registers can be specified as x0–x31 or ABI names (zero, ra, sp, a0 … t6)
- Immediates can be decimal (10) or hexadecimal (0xFF)
- Comments start with # and are ignored
- Blank lines are ignored

Raises ValueError if an unknown instruction is encountered.
"""

_pc = 0         # program counter
_labels = {}    # stores a label and address associated with that label

# Used when instruction operand can either be a label or numerical literal
# If the label is in labels, it returns an offset from the current PC
# Otherwise, it parses the label as a plain interger
def _int_or_label(label) -> int:
    if label in _labels:
        return _labels[label] - _pc

    return int(label, 0)

# Register Instruction
# funct7(7b) | rs2(5b) | rs1(5b) | funct3(3b) | opcode(7b)
def _encode_R(funct7, rs2, rs1, funct3, rd, opcode) -> int:
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
def _encode_I(imm, rs1, funct3, rd, opcode) -> int:
    return (
        ((imm & 0b111111111111) << 20) |  # imm[11:0] - bits 31-20
        ((rs1 & 0b11111) << 15) |
        ((funct3 & 0b111) << 12) |
        ((rd & 0b11111) << 7) |
        (opcode & 0b1111111)
    )

# Store Instruction
# imm[11:5] | rs2(5b) | rs1(5b) | funct3(3b) | imm[4:0] | opcode(7b)
def _encode_S(imm, rs2, rs1, funct3, opcode) -> int:
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
def _encode_B(imm, rs2, rs1, funct3, opcode) -> int:
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
def _encode_U(imm, rd, opcode) -> int:
    return (
        ((imm & 0b11111111111111111111) << 12) |  # imm[19:0]
        ((rd & 0b11111) << 7) |
        (opcode & 0b1111111)
    )

# Unconditional Jump
# imm[20] | imm[10:1] | imm[11] | imm[19:12] | rd(5b) | opcode(7b)
def _encode_J(imm, rd, opcode) -> int:
    return (
        (((imm >> 20) & 0b1) << 31) |  # imm[20]
        (((imm >> 1) & 0b1111111111) << 21) |  # imm[10:1]
        (((imm >> 11) & 0b1) << 20) |  # imm[11]
        (((imm >> 12) & 0b11111111) << 12) |  # imm[19:12]
        ((rd & 0b11111) << 7) |
        (opcode & 0b1111111)
    )

# Application Binary Interface
ABI = {name: i for i, name in enumerate(REGISTER_NAMES)}

# Converts register token into its index (0-31)
# It handles both numeric names (x5) and ABI (t0, sp, a0) by looking up the ABI dict built from REGISTER_NAMES
def _reg(name: str) -> int:
    name = name.strip().lower()
    if name in ABI:
        return ABI[name]
    return int(name[1:])

# This is the main function that handles one real (non-pseudo) instruction string
#
# It splits the line into tokens, reads the mnemonic, and 
# dispatches to the appropriate _encode_* function with the right fields
#
# It raises ValueError for any unrecognized mnemonic
def _assemble_line(instruction: str) -> int:
    parts = instruction.replace(",", "").split()
    mnemonic = parts[0].lower()

    # ——————————————————— R-Type ———————————————————
    if mnemonic == "add":
        return _encode_R(0b0000000, _reg(parts[3]), _reg(parts[2]), 0b000, _reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "sub":
        return _encode_R(0b0100000, _reg(parts[3]), _reg(parts[2]), 0b000, _reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "sll":
        return _encode_R(0b0000000, _reg(parts[3]), _reg(parts[2]), 0b001, _reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "slt":
        return _encode_R(0b0000000, _reg(parts[3]), _reg(parts[2]), 0b010, _reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "sltu":
        return _encode_R(0b0000000, _reg(parts[3]), _reg(parts[2]), 0b011, _reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "xor":
        return _encode_R(0b0000000, _reg(parts[3]), _reg(parts[2]), 0b100, _reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "srl":
        return _encode_R(0b0000000, _reg(parts[3]), _reg(parts[2]), 0b101, _reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "sra":
        return _encode_R(0b0100000, _reg(parts[3]), _reg(parts[2]), 0b101, _reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "or":
        return _encode_R(0b0000000, _reg(parts[3]), _reg(parts[2]), 0b110, _reg(parts[1]), InstructionOpcodes.OPreg)
    elif mnemonic == "and":
        return _encode_R(0b0000000, _reg(parts[3]), _reg(parts[2]), 0b111, _reg(parts[1]), InstructionOpcodes.OPreg)

    # ——————————————————— I-Type ALU ———————————————————
    elif mnemonic == "addi":
        return _encode_I(int(parts[3], 0), _reg(parts[2]), 0b000, _reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "slti":
        return _encode_I(int(parts[3], 0), _reg(parts[2]), 0b010, _reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "sltiu":
        return _encode_I(int(parts[3], 0), _reg(parts[2]), 0b011, _reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "xori":
        return _encode_I(int(parts[3], 0), _reg(parts[2]), 0b100, _reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "ori":
        return _encode_I(int(parts[3], 0), _reg(parts[2]), 0b110, _reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "andi":
        return _encode_I(int(parts[3], 0), _reg(parts[2]), 0b111, _reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "slli":
        return _encode_I(int(parts[3], 0) & 0b11111, _reg(parts[2]), 0b001, _reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "srli":
        return _encode_I(int(parts[3], 0) & 0b11111, _reg(parts[2]), 0b101, _reg(parts[1]), InstructionOpcodes.OPimm)
    elif mnemonic == "srai":
        # srai encodes funct7=0100000 in the upper 7 bits of the immediate
        return _encode_I((0b0100000 << 5) | (int(parts[3], 0) & 0b11111), _reg(parts[2]), 0b101, _reg(parts[1]), InstructionOpcodes.OPimm)

    # ——————————————————— I-Type LOAD ———————————————————
    elif mnemonic in ["lw", "lh", "lb", "lbu", "lhu"]:
        offset, rs1 = parts[2].split("(")
        rs1 = rs1.strip(")")
        funct3 = {"lb": 0b000, "lh": 0b001, "lw": 0b010,
                  "lbu": 0b100, "lhu": 0b101}[mnemonic]
        return _encode_I(int(offset, 0), _reg(rs1), funct3, _reg(parts[1]), InstructionOpcodes.LOAD)

    # ——————————————————— I-Type JALR ———————————————————
    elif mnemonic == "jalr":
        return _encode_I(int(parts[3], 0), _reg(parts[2]), 0b000, _reg(parts[1]), InstructionOpcodes.JALR)

    # ——————————————————— I-Type System ———————————————————
    elif mnemonic == "ecall":
        return _encode_I(0, 0, 0b000, 0, InstructionOpcodes.SYSTEM)
    elif mnemonic == "ebreak":
        return _encode_I(1, 0, 0b000, 0, InstructionOpcodes.SYSTEM)

    # ——————————————————— S-Type Store ———————————————————
    elif mnemonic in ["sw", "sh", "sb"]:
        offset, rs1 = parts[2].split("(")
        rs1 = rs1.strip(")")
        funct3 = {"sw": 0b010, "sh": 0b001, "sb": 0b000}[mnemonic]
        return _encode_S(int(offset, 0), _reg(parts[1]), _reg(rs1), funct3, InstructionOpcodes.STORE)

    # ——————————————————— B-Type Branch ———————————————————
    elif mnemonic in ["beq", "bne", "blt", "bge", "bltu", "bgeu"]:
        funct3 = {"beq": 0b000, "bne": 0b001, "blt": 0b100,
                  "bge": 0b101, "bltu": 0b110, "bgeu": 0b111}[mnemonic]
        return _encode_B(_int_or_label(parts[3]), _reg(parts[2]), _reg(parts[1]), funct3, InstructionOpcodes.BRANCH)

    # ——————————————————— U-Type Branch ———————————————————
    elif mnemonic == "lui":
        return _encode_U(int(parts[2], 0), _reg(parts[1]), InstructionOpcodes.LUI)
    elif mnemonic == "auipc":
        return _encode_U(int(parts[2], 0), _reg(parts[1]), InstructionOpcodes.AUIPC)

    # ——————————————————— J-Type Branch ———————————————————
    elif mnemonic == "jal":
        return _encode_J(_int_or_label(parts[2]), _reg(parts[1]), InstructionOpcodes.JAL)

    raise ValueError(f"Unknown Instruction: {mnemonic}")

# Predicts how many 32-bit words a line will emit without actually assembling it
# This is needed during the label-scanning pass so that label addresses 
# can be calculated correctly before any encoding happens
# 
# la always expands to 2 words
# li expands to 1 or 2 depending on whether the immediate fits in 12 bits
# everything else is 1
def _pseudo_size(line: str) -> int:
    parts = line.replace(",", "").split()
    if not parts:
        return 0
    instr_temp = parts[0].lower()
    if instr_temp == "la":
        return 2
    if instr_temp == "li":
        try:
            imm = int(parts[2], 0)
            return 1 if -2048 <= imm <= 2047 else 2
        except (IndexError, ValueError):
            return 1
    return 1

# Expands pseudo-instructions into real machine words
def _assemble_pseudo(line: str) -> list[int]:
    parts = line.replace(",", "").split()
    if not parts:
        return []
    instr_temp = parts[0].lower()

    # la is expanded into the two instructions because RISC-V address is 32-bit long

    # la rd, symbol
    #   -> lui rd, %hi(addr)
    #   -> addi rd, rd, %lo(addr)
    if instr_temp == "la":
        rd = _reg(parts[1])
        addr = _labels[parts[2]]
        upper = (addr + 0x800) >> 12  # upper 20 bits (with rounding)
        # lower 12 bits (signed, range -2048..2047)
        lower = addr - (upper << 12)

        instr1 = (_encode_U(upper & 0xFFFFF, rd, InstructionOpcodes.LUI)
                  if upper else
                  _encode_I(0, 0, 0b000, rd, InstructionOpcodes.OPimm))
        instr2 = _encode_I(lower, rd, 0b000, rd, InstructionOpcodes.OPimm)
        return [instr1, instr2]

    # For small immediates (12 bit signed), li uses only one instruction.
    # For large immediates (up to 32-bit), li uses two instructions.
    #
    # li rd, imm
    #   -> li rd, imm  addi rd, x0, imm                 (small)
    #   -> lui rd, %hi(imm)  +  addi rd, rd, %lo(imm)   (large)
    if instr_temp == "li":
        rd = _reg(parts[1])
        imm = int(parts[2], 0)
        if -2048 <= imm <= 2047:    # check if the immediate value is small
            return [_encode_I(imm, 0, 0b000, rd, InstructionOpcodes.OPimm)]
        upper = (imm + 0x800) >> 12
        lower = imm - (upper << 12)
        return [
            _encode_U(upper & 0xFFFFF, rd, InstructionOpcodes.LUI),
            _encode_I(lower, rd, 0b000, rd, InstructionOpcodes.OPimm),
        ]

    # mv rd, rs -> addi rd, rs, 0
    if instr_temp == "mv":
        rd = _reg(parts[1])
        rs = _reg(parts[2])
        return [_encode_I(0, rs, 0b000, rd, InstructionOpcodes.OPimm)]

    # j label -> jal x0, offset
    if instr_temp == "j":
        return [_encode_J(_int_or_label(parts[1]), 0, InstructionOpcodes.JAL)]

    # ret -> jalr x0, ra, 0
    if instr_temp == "ret":
        return [_encode_I(0, ABI["ra"], 0b000, 0, InstructionOpcodes.JALR)]

    # nop  →  addi x0, x0, 0
    if instr_temp == "nop":
        return [_encode_I(0, 0, 0b000, 0, InstructionOpcodes.OPimm)]

    # Anything else is a real instruction
    return [_assemble_line(line)]


_ESCAPES = {"n": 10, "t": 9, "r": 13, "0": 0, "\\": 92, '"': 34, "'": 39}

# Converts a quoted string literal (like "hello\n") into a list of byte values
# Handles standard escape sequences via the _ESCAPES lookup table.
#
# _parse_string('"hi\n"')
# 'h' -> 104, 'i' -> 105, '\n' -> 10
# returns [104, 105, 10]
def _parse_string(raw: str) -> list[int]:
    s = raw.strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    chars = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            chars.append(_ESCAPES.get(s[i+1], ord(s[i+1])))
            i += 2
        else:
            chars.append(ord(s[i]))
            i += 1
    return chars

# Takes a list of bytes and packs every four of them into one little-endian (LSB at the lowest memory address) 32-bit word
# which is how strings get stored in the data section
#
# _pack_bytes_to_words([104, 105, 10, 0])
# packs little-endian: byte0 | byte1<<8 | byte2<<16 | byte3<<24
# 104 | (105 << 8) | (10 << 16) | (0 << 24)
# returns [673897576]
def _pack_bytes_to_words(byte_vals: list[int]) -> list[int]:
    words = []
    for i in range(0, len(byte_vals), 4):
        words.append(
            byte_vals[i]
            | (byte_vals[i + 1] << 8)
            | (byte_vals[i + 2] << 16)
            | (byte_vals[i + 3] << 24)
        )
    return words

# Handles a single .data directive line and returns the list of 32-bit words it produces
#
# It dispatches on the directive type: .word parses comma-separated integers, 
# while .asciz/.string call _parse_string, append a null terminator, pad to a 4-byte boundary, 
# then call _pack_bytes_to_words. .ascii is the same but skips the null terminator.
#
# _data_words(".word 1, 2, 3")
# returns [1, 2, 3]
#
# _data_words('.asciz "hi\n"')
# calls _parse_string -> [104, 105, 10]
# appends null terminator -> [104, 105, 10, 0]
# already 4 bytes so no padding needed
# calls _pack_bytes_to_words ->[673897576]
# returns [673897576]
def _data_words(line: str) -> list[int]:
    parts = line.split(None, 1)
    directive = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    if directive == ".word":
        return [int(v.strip(), 0) & 0xFFFFFFFF for v in args.split(",") if v.strip()]

    if directive in (".asciz", ".string", ".ascii"):
        byte_vals = _parse_string(args)
        if directive != ".ascii":
            byte_vals.append(0)
        while len(byte_vals) % 4:
            byte_vals.append(0)
        return _pack_bytes_to_words(byte_vals)

    return []

#  _data_size(line) returns the byte size of what _data_words would emit 
# used during the first pass to calculate data-label addresses.
def _data_size(line: str) -> int:
    return len(_data_words(line)) * 4

# First pass 
# It splits lines into .text and .data buckets, then walks each bucket to build the _labels dictionary 
# Text labels get addresses in units of 4 bytes (one per instruction word). 
# Data labels get addresses starting right after the text section, 
# accounting for the variable size of .word and string directives.
# 
# Second pass
# It walks the text lines again, calls _assemble_pseudo 
# on each non-label line (which itself calls _assemble_line for real instructions), and collects the resulting words. 
# Then it walks the data lines and appends words from _data_words.
# 
# The final flat list of 32-bit integers is returned, ready to be written into the memory model.
def assemble(source: str) -> list[int]:
    global _pc
    global _labels
    _pc = 0
    _labels.clear() # choose .clear() because _labels = {} creates a new local variable
    words = []

    text_lines = []
    data_lines = []
    current = "text"

    # Inserts instructions either in text_lines or data_lines
    for raw in source.strip().splitlines():
        line = raw.split("#")[0].strip() # doesn't include comments in a line
        if not line:
            continue
        low = line.lower()
        if low == ".data":
            current = "data"
            continue
        if low == ".text":
            current = "text"
            continue
        (text_lines if current == "text" else data_lines).append(line)

    # Inserts text labels and their addresses
    text_pc = 0
    for line in text_lines:
        if ":" in line:
            label, _, rest = line.partition(":")
            _labels[label.strip()] = text_pc
            rest = rest.strip()
            if rest:
                text_pc += _pseudo_size(rest) * 4
        else:
            text_pc += _pseudo_size(line) * 4

    # Inserts data labels and their addresses
    data_start = text_pc
    data_pc = data_start
    for line in data_lines:
        if ":" in line:
            label, _, rest = line.partition(":")
            _labels[label.strip()] = data_pc
            rest = rest.strip()
            if rest:
                data_pc += _data_size(rest)
        else:
            data_pc += _data_size(line)

    # Executes instructions 
    for line in text_lines:
        if ":" in line: 
            _, _, rest = line.partition(":") # if there is an instruction after a label
            rest = rest.strip()
            if rest:
                emitted = _assemble_pseudo(rest)
                words.extend(emitted)
                _pc += len(emitted) * 4
        else:
            emitted = _assemble_pseudo(line)
            words.extend(emitted)
            _pc += len(emitted) * 4

    # Encodes each data section line into 32-bit words, 
    # stripping any label prefix before passing the directive to _data_words.
    for line in data_lines:
        if ":" in line:
            _, _, rest = line.partition(":")
            rest = rest.strip()
            if rest:
                words.extend(_data_words(rest))
        else:
            words.extend(_data_words(line))

    return words


def main():
    source = "add x1, x2, x3 \n add x5, x5, x6 \n label: \n add x5, x5, x6 \n jal x1 label"
    words = assemble(source)
    print(words)
    print(_labels)


if __name__ == "__main__":
    main()
