from riscv.isa import *
from riscv.parser import ParsedLine, ParseError, parse_int

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

class Assembler:

    def __init__(self, ):
        self._pc = 0
        self._labels = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assemble(self, parsed_lines: list[ParsedLine], symbol_table: dict[str, int]) -> list[int]:
        self._pc = 0
        words = []
        data_lines = []

        self._labels = symbol_table

        # Assemble instructions
        for parsed_line in parsed_lines:
            mnemonic = parsed_line.mnemonic
            operands = parsed_line.operands

            # Since the parser adds text lines first, we iterate through them first. Then, we go to data lines.
            if mnemonic in DIRECTIVES - {".data", ".text"}:
                # Encode data directly into words
                words.extend(parsed_line.data_words)
            else:
                # Encode instruction
                emitted = self._assemble_pseudo([mnemonic] + operands)
                words.extend(emitted)
                self._pc += len(emitted) * 4
        return words

    # ------------------------------------------------------------------
    # Private helpers — encoding
    # ------------------------------------------------------------------

    # Register Instruction
    # funct7(7b) | rs2(5b) | rs1(5b) | funct3(3b) | opcode(7b)
    def _encode_R(self, funct7, rs2, rs1, funct3, rd, opcode) -> int:
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
    def _encode_I(self, imm, rs1, funct3, rd, opcode) -> int:
        return (
            ((imm & 0b111111111111) << 20) |  # imm[11:0] - bits 31-20
            ((rs1 & 0b11111) << 15) |
            ((funct3 & 0b111) << 12) |
            ((rd & 0b11111) << 7) |
            (opcode & 0b1111111)
        )

    # Store Instruction
    # imm[11:5] | rs2(5b) | rs1(5b) | funct3(3b) | imm[4:0] | opcode(7b)
    def _encode_S(self, imm, rs2, rs1, funct3, opcode) -> int:
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
    def _encode_B(self, imm, rs2, rs1, funct3, opcode) -> int:
        return (
            (((imm >> 12) & 0b1) << 31) |       # imm[12]
            (((imm >> 5) & 0b111111) << 25) |   # imm[10:5]
            ((rs2 & 0b11111) << 20) |
            ((rs1 & 0b11111) << 15) |
            ((funct3 & 0b111) << 12) |
            (((imm >> 1) & 0b1111) << 8) |      # imm[4:1]
            (((imm >> 11) & 0b1) << 7) |        # imm[11]
            (opcode & 0b1111111)
        )

    # Upper Immediate Instruction
    # imm[31:12] | rd(5b) | opcode(7b)
    def _encode_U(self, imm, rd, opcode) -> int:
        return (
            ((imm & 0b11111111111111111111) << 12) |  # imm[19:0]
            ((rd & 0b11111) << 7) |
            (opcode & 0b1111111)
        )

    # Unconditional Jump
    # imm[20] | imm[10:1] | imm[11] | imm[19:12] | rd(5b) | opcode(7b)
    def _encode_J(self, imm, rd, opcode) -> int:
        return (
            (((imm >> 20) & 0b1) << 31) |              # imm[20]
            (((imm >> 1) & 0b1111111111) << 21) |      # imm[10:1]
            (((imm >> 11) & 0b1) << 20) |              # imm[11]
            (((imm >> 12) & 0b11111111) << 12) |       # imm[19:12]
            ((rd & 0b11111) << 7) |
            (opcode & 0b1111111)
        )

    # ------------------------------------------------------------------
    # Private helpers — registers and labels
    # ------------------------------------------------------------------

    # Converts register token into its index (0-31)
    # It handles both numeric names (x5) and ABI names (t0, sp, a0, fp)
    def _reg(self, name: str) -> int:
        name = name.strip().lower()
        if name not in REGISTER_INDEX:
            raise ValueError(f"Invalid register: '{name}'")
        return REGISTER_INDEX[name]

    # Used when instruction operand can either be a label or numerical literal
    # If the label is in labels, it returns an offset from the current PC
    # Otherwise, it parses the label as a plain integer
    def _int_or_label(self, label) -> int:
        if label in self._labels:
            return self._labels[label] - self._pc
        return parse_int(label)

    # Raises ValueError when an immediate/offset doesn't fit its encoding —
    # without this the encoders would silently truncate it to a different value
    @staticmethod
    def _check_range(value: int, lo: int, hi: int, what: str, even: bool = False) -> int:
        if not (lo <= value <= hi):
            raise ValueError(f"{what} {value} out of range ({lo} to {hi})")
        if even and value % 2 != 0:
            raise ValueError(f"{what} {value} must be even")
        return value

    # 12-bit signed immediate shared by I-type ALU ops, loads, stores, and jalr
    def _imm12(self, value: int, mnemonic: str) -> int:
        return self._check_range(value, -2048, 2047, f"Immediate for '{mnemonic}'")

    # 5-bit shift amount for slli/srli/srai
    def _shamt(self, value: int, mnemonic: str) -> int:
        return self._check_range(value, 0, 31, f"Shift amount for '{mnemonic}'")

    # ------------------------------------------------------------------
    # Private helpers — assembly
    # ------------------------------------------------------------------

    # This is the main function that handles one real (non-pseudo) instruction string
    #
    # It splits the line into tokens, reads the mnemonic, and
    # dispatches to the appropriate _encode_* function with the right fields
    #
    # It raises ValueError for any unrecognized mnemonic
    def _assemble_line(self, parts: list[str]) -> int:
        mnemonic = parts[0].lower()

        # ——————————————————— R-Type ———————————————————
        if mnemonic == "add":
            return self._encode_R(0b0000000, self._reg(parts[3]), self._reg(parts[2]), 0b000, self._reg(parts[1]), InstructionOpcodes.OPreg)
        elif mnemonic == "sub":
            return self._encode_R(0b0100000, self._reg(parts[3]), self._reg(parts[2]), 0b000, self._reg(parts[1]), InstructionOpcodes.OPreg)
        elif mnemonic == "sll":
            return self._encode_R(0b0000000, self._reg(parts[3]), self._reg(parts[2]), 0b001, self._reg(parts[1]), InstructionOpcodes.OPreg)
        elif mnemonic == "slt":
            return self._encode_R(0b0000000, self._reg(parts[3]), self._reg(parts[2]), 0b010, self._reg(parts[1]), InstructionOpcodes.OPreg)
        elif mnemonic == "sltu":
            return self._encode_R(0b0000000, self._reg(parts[3]), self._reg(parts[2]), 0b011, self._reg(parts[1]), InstructionOpcodes.OPreg)
        elif mnemonic == "xor":
            return self._encode_R(0b0000000, self._reg(parts[3]), self._reg(parts[2]), 0b100, self._reg(parts[1]), InstructionOpcodes.OPreg)
        elif mnemonic == "srl":
            return self._encode_R(0b0000000, self._reg(parts[3]), self._reg(parts[2]), 0b101, self._reg(parts[1]), InstructionOpcodes.OPreg)
        elif mnemonic == "sra":
            return self._encode_R(0b0100000, self._reg(parts[3]), self._reg(parts[2]), 0b101, self._reg(parts[1]), InstructionOpcodes.OPreg)
        elif mnemonic == "or":
            return self._encode_R(0b0000000, self._reg(parts[3]), self._reg(parts[2]), 0b110, self._reg(parts[1]), InstructionOpcodes.OPreg)
        elif mnemonic == "and":
            return self._encode_R(0b0000000, self._reg(parts[3]), self._reg(parts[2]), 0b111, self._reg(parts[1]), InstructionOpcodes.OPreg)

        # ——————————————————— I-Type ALU ———————————————————
        elif mnemonic == "addi":
            return self._encode_I(self._imm12(parse_int(parts[3]), mnemonic), self._reg(parts[2]), 0b000, self._reg(parts[1]), InstructionOpcodes.OPimm)
        elif mnemonic == "slti":
            return self._encode_I(self._imm12(parse_int(parts[3]), mnemonic), self._reg(parts[2]), 0b010, self._reg(parts[1]), InstructionOpcodes.OPimm)
        elif mnemonic == "sltiu":
            return self._encode_I(self._imm12(parse_int(parts[3]), mnemonic), self._reg(parts[2]), 0b011, self._reg(parts[1]), InstructionOpcodes.OPimm)
        elif mnemonic == "xori":
            return self._encode_I(self._imm12(parse_int(parts[3]), mnemonic), self._reg(parts[2]), 0b100, self._reg(parts[1]), InstructionOpcodes.OPimm)
        elif mnemonic == "ori":
            return self._encode_I(self._imm12(parse_int(parts[3]), mnemonic), self._reg(parts[2]), 0b110, self._reg(parts[1]), InstructionOpcodes.OPimm)
        elif mnemonic == "andi":
            return self._encode_I(self._imm12(parse_int(parts[3]), mnemonic), self._reg(parts[2]), 0b111, self._reg(parts[1]), InstructionOpcodes.OPimm)
        elif mnemonic == "slli":
            return self._encode_I(self._shamt(parse_int(parts[3]), mnemonic), self._reg(parts[2]), 0b001, self._reg(parts[1]), InstructionOpcodes.OPimm)
        elif mnemonic == "srli":
            return self._encode_I(self._shamt(parse_int(parts[3]), mnemonic), self._reg(parts[2]), 0b101, self._reg(parts[1]), InstructionOpcodes.OPimm)
        elif mnemonic == "srai":
            # srai encodes funct7=0100000 in the upper 7 bits of the immediate
            return self._encode_I((0b0100000 << 5) | self._shamt(parse_int(parts[3]), mnemonic), self._reg(parts[2]), 0b101, self._reg(parts[1]), InstructionOpcodes.OPimm)

        # ——————————————————— I-Type LOAD ———————————————————
        elif mnemonic in ["lw", "lh", "lb", "lbu", "lhu"]:
            offset, rs1 = parts[2].split("(")
            rs1 = rs1.strip(")")
            funct3 = {"lb": 0b000, "lh": 0b001, "lw": 0b010,
                      "lbu": 0b100, "lhu": 0b101}[mnemonic]
            # "(x2)" with no offset means offset 0
            return self._encode_I(self._imm12(parse_int(offset) if offset else 0, mnemonic), self._reg(rs1), funct3, self._reg(parts[1]), InstructionOpcodes.LOAD)

        # ——————————————————— I-Type JALR ———————————————————
        elif mnemonic == "jalr":
            return self._encode_I(self._imm12(parse_int(parts[3]), mnemonic), self._reg(parts[2]), 0b000, self._reg(parts[1]), InstructionOpcodes.JALR)

        # ——————————————————— I-Type System ———————————————————
        elif mnemonic == "ecall":
            return self._encode_I(0, 0, 0b000, 0, InstructionOpcodes.SYSTEM)
        elif mnemonic == "ebreak":
            return self._encode_I(1, 0, 0b000, 0, InstructionOpcodes.SYSTEM)

        # ——————————————————— S-Type Store ———————————————————
        elif mnemonic in ["sw", "sh", "sb"]:
            offset, rs1 = parts[2].split("(")
            rs1 = rs1.strip(")")
            funct3 = {"sw": 0b010, "sh": 0b001, "sb": 0b000}[mnemonic]
            return self._encode_S(self._imm12(parse_int(offset) if offset else 0, mnemonic), self._reg(parts[1]), self._reg(rs1), funct3, InstructionOpcodes.STORE)

        # ——————————————————— B-Type Branch ———————————————————
        elif mnemonic in ["beq", "bne", "blt", "bge", "bltu", "bgeu"]:
            funct3 = {"beq": 0b000, "bne": 0b001, "blt": 0b100,
                      "bge": 0b101, "bltu": 0b110, "bgeu": 0b111}[mnemonic]
            offset = self._check_range(self._int_or_label(parts[3]), -4096, 4094,
                                       f"Branch offset for '{mnemonic}'", even=True)
            return self._encode_B(offset, self._reg(parts[2]), self._reg(parts[1]), funct3, InstructionOpcodes.BRANCH)

        # ——————————————————— U-Type ———————————————————
        elif mnemonic == "lui":
            return self._encode_U(self._check_range(parse_int(parts[2]), 0, 0xFFFFF, f"Immediate for '{mnemonic}'"), self._reg(parts[1]), InstructionOpcodes.LUI)
        elif mnemonic == "auipc":
            return self._encode_U(self._check_range(parse_int(parts[2]), 0, 0xFFFFF, f"Immediate for '{mnemonic}'"), self._reg(parts[1]), InstructionOpcodes.AUIPC)

        # ——————————————————— J-Type ———————————————————
        elif mnemonic == "jal":
            offset = self._check_range(self._int_or_label(parts[2]), -1048576, 1048574,
                                       "Jump offset for 'jal'", even=True)
            return self._encode_J(offset, self._reg(parts[1]), InstructionOpcodes.JAL)

        raise ValueError(f"Unknown Instruction: {mnemonic}")

    # Expands pseudo-instructions into real machine words
    def _assemble_pseudo(self, parts: list[str]) -> list[int]:
        if not parts:
            return []
        instr_temp = parts[0].lower()

        # la is expanded into the two instructions because RISC-V address is 32-bit long

        # la rd, symbol
        #   -> lui rd, %hi(addr)
        #   -> addi rd, rd, %lo(addr)
        if instr_temp == "la":
            rd = self._reg(parts[1])
            addr = self._labels[parts[2]]
            upper = (addr + 0x800) >> 12  # upper 20 bits (with rounding)
            # lower 12 bits (signed, range -2048..2047)
            lower = addr - (upper << 12)

            instr1 = (self._encode_U(upper & 0xFFFFF, rd, InstructionOpcodes.LUI)
                      if upper else
                      self._encode_I(0, 0, 0b000, rd, InstructionOpcodes.OPimm))
            instr2 = self._encode_I(
                lower, rd, 0b000, rd, InstructionOpcodes.OPimm)
            return [instr1, instr2]

        # For small immediates (12 bit signed), li uses only one instruction.
        # For large immediates (up to 32-bit), li uses two instructions.
        #
        # li rd, imm
        #   -> addi rd, x0, imm                 (small)
        #   -> lui rd, %hi(imm)  +  addi rd, rd, %lo(imm)   (large)
        if instr_temp == "li":
            rd = self._reg(parts[1])
            imm = self._check_range(parse_int(parts[2]), -2147483648, 4294967295,
                                    "Immediate for 'li'")
            if -2048 <= imm <= 2047:  # check if the immediate value is small
                return [self._encode_I(imm, 0, 0b000, rd, InstructionOpcodes.OPimm)]
            upper = (imm + 0x800) >> 12
            lower = imm - (upper << 12)
            return [
                self._encode_U(upper & 0xFFFFF, rd, InstructionOpcodes.LUI),
                self._encode_I(lower, rd, 0b000, rd, InstructionOpcodes.OPimm),
            ]

        # mv rd, rs -> addi rd, rs, 0
        if instr_temp == "mv":
            rd = self._reg(parts[1])
            rs = self._reg(parts[2])
            return [self._encode_I(0, rs, 0b000, rd, InstructionOpcodes.OPimm)]

        # j label -> jal x0, offset
        if instr_temp == "j":
            offset = self._check_range(self._int_or_label(parts[1]), -1048576, 1048574,
                                       "Jump offset for 'j'", even=True)
            return [self._encode_J(offset, 0, InstructionOpcodes.JAL)]

        # ret -> jalr x0, ra, 0
        if instr_temp == "ret":
            return [self._encode_I(0, REGISTER_INDEX["ra"], 0b000, 0, InstructionOpcodes.JALR)]

        # nop  →  addi x0, x0, 0
        if instr_temp == "nop":
            return [self._encode_I(0, 0, 0b000, 0, InstructionOpcodes.OPimm)]

        # Anything else is a real instruction
        return [self._assemble_line(parts)]


def main():
    from riscv.parser import Parser
    source = "add x1, x2, x3 \n add x5, x5, x6 \n label: \n add x5, x5, x6 \n jal x1 label"
    parser = Parser()
    parsed_lines = parser.parse(source)
    assembler = Assembler()
    words = assembler.assemble(parsed_lines, parser.symbol_table)
    print(assembler._reg("x1"))   # should be 1
    print(assembler._reg("x2"))   # should be 2
    print(assembler._reg("x3"))   # should be 3
    print(assembler._reg("x5"))   # should be 5
    print(assembler._reg("x6"))   # should be 6
    print(words)
    print(parser.symbol_table)


if __name__ == "__main__":
    main()
