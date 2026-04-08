from riscv.isa import *
from riscv.assembler import *

"""
Implements a RISC-V RV32I instruction decoder.

Takes a 32-bit machine code word and decodes it into its constituent fields
based on the instruction format (R, I, S, B, U, J).

Decoded fields include:
- opcode: identifies the instruction type
- rd, rs1, rs2: destination and source register indices
- funct3, funct7: sub-operation selectors
- imm: sign-extended immediate value (format-dependent)
- mnemonic: human-readable instruction name (e.g. "addi", "lw", "beq")

Immediate decoding handles all 6 RV32I formats:
- R-type: no immediate (register-register operations)
- I-type: 12-bit sign-extended immediate
- S-type: 12-bit immediate split across two fields
- B-type: 13-bit PC-relative branch offset, bits scattered across the word
- U-type: 20-bit upper immediate
- J-type: 21-bit PC-relative jump offset, bits scattered across the word
"""


def to_signed(value, bits):
    if value >= (1 << (bits - 1)):
        value -= (1 << bits)
    return value


class DecodedInstruction:
    def __init__(self, instruction):
        # Initialize instruction fields
        self.opcode = instruction & 0b1111111
        self.rd = (instruction >> 7) & 0b11111
        self.funct3 = (instruction >> 12) & 0b111
        self.rs1 = (instruction >> 15) & 0b11111
        self.rs2 = (instruction >> 20) & 0b11111
        self.funct7 = (instruction >> 25) & 0b1111111

        # Initialize the flags of each instruction opcode
        # rd <- rs1 OP rs2
        self.isOPreg = (self.opcode == InstructionOpcodes.OPreg)
        # rd <- rs1 OP Iimm
        self.isOPimm = (self.opcode == InstructionOpcodes.OPimm)
        # rd <- mem[rs1 + Iimm]
        self.isLoad = (self.opcode == InstructionOpcodes.LOAD)
        # mem[rs1 + Simm] <- rs2
        self.isStore = (self.opcode == InstructionOpcodes.STORE)
        # if (rs1 OP rs2) PC <- PC + Bimm
        self.isBranch = (self.opcode == InstructionOpcodes.BRANCH)
        # rd <- PC+4; PC <- rs1 + Jimm
        self.isJal = (self.opcode == InstructionOpcodes.JAL)
        # rd <- PC+4; PC <- Iimm
        self.isJalr = (self.opcode == InstructionOpcodes.JALR)
        # rd <- Uimm
        self.isLUI = (self.opcode == InstructionOpcodes.LUI)
        # rd <- PC + Uimm
        self.isAUIPC = (self.opcode == InstructionOpcodes.AUIPC)
        self.isSystem = (self.opcode == InstructionOpcodes.SYSTEM)  # special

        # inst[31:20] sign-extended to 32 bits
        self.Iimm = to_signed((instruction >> 20), 12)
        
        # inst[31:25] + inst[11:7]
        self.Simm = to_signed(((instruction >> 25) << 5)
                              | ((instruction >> 7) & 0b11111), 12)
        
        # inst[31] + inst[7] + inst[30:25] + inst[11:8] + 0
        self.Bimm = to_signed(
            (((instruction >> 31) & 1) << 12) |
            (((instruction >> 7) & 1) << 11) |
            (((instruction >> 25) & 0b111111) << 5) |
            (((instruction >> 8) & 0b1111) << 1),
            13)
        
        # inst[31:12] + 12 zeros
        self.Uimm = (instruction >> 12) & 0xFFFFF
        
        # inst[31] + inst[19:12] + inst[20] + inst[30:21] + 0
        self.Jimm = to_signed(
            (((instruction >> 31) & 1) << 20) |
            (((instruction >> 12) & 0xFF) << 12) |
            (((instruction >> 20) & 1) << 11) |
            (((instruction >> 21) & 0x3FF) << 1),
            21)


def main():

    # Print fields of decoded instruction
    def print_decoded_instr(self):
        print("========= Decoded Instruction =========")
        print(f"Opcode: {self.opcode:07b}")
        print(f"rd:     {self.rd:05b}")
        print(f"funct3: {self.funct3:03b}")
        print(f"rs1:    {self.rs1:05b}")
        print(f"rs2:    {self.rs2:05b}")
        print(f"funct7: {self.funct7:07b}")

    # Print the type of an instruction
    def print_instr_opcode(self):
        flags = {
            "isOPreg": self.isOPreg, "isOPimm": self.isOPimm,
            "isLoad": self.isLoad,   "isStore": self.isStore,
            "isBranch": self.isBranch, "isJal": self.isJal,
            "isJalr": self.isJalr,  "isLUI": self.isLUI,
            "isAUIPC": self.isAUIPC, "isSystem": self.isSystem
        }

        print("========= Print Instruction Flags =========")
        for name, value in flags.items():
            print(f"{name}: {value}")

    # Print the type of instruction immediate
    def print_instr_imm(self):
        print("Immediate Type: " + OPCODE_FORMATS.get(self.opcode) + "imm")

    # Print the instruction itself
    def print_instr(self):
        print("========= Print Instruction =========")
        mnemonic = MNEMONICS.get((self.opcode, self.funct3, self.funct7)) or MNEMONICS.get(
            (self.opcode, None)) or MNEMONICS.get((self.opcode, self.funct3), "unknown")
        print(mnemonic)

    source = "add x1, x2, x3 \n add x5, x5, x6 \n label: \n add x5, x5, x6 \n jal x1 label"
    decoded_instructions = []
    instructions = assemble(source)
    for instr in instructions:
        new_decoded_instr = DecodedInstruction(instr)
        decoded_instructions.append(new_decoded_instr)
        print_instr_opcode(new_decoded_instr)
        print_decoded_instr(new_decoded_instr)
        print_instr(new_decoded_instr)
        print_instr_imm(new_decoded_instr)
        print("\n")


if __name__ == "__main__":
    main()
