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
class DecodedInstruction:
    def __init__(self, instruction):
        # Convert a instruction code into a 32-bit string of binary numbers
        instruction = format(instruction, '032b')

        # Initialize instruction fields
        self.opcode = int(instruction[25:], 2)
        self.rd = int(instruction[20:25], 2)
        self.funct3 = int(instruction[17:20], 2)
        self.rs1 = int(instruction[12:17], 2)
        self.rs2 = int(instruction[7:12], 2)
        self.funct7 = int(instruction[0:7], 2)

        # Initialize the flags of each instruction opcode
        self.isOPreg = (self.opcode == InstructionOpcodes.OPreg)    # rd <- rs1 OP rs2
        self.isOPimm = (self.opcode == InstructionOpcodes.OPimm)    # rd <- rs1 OP Iimm
        self.isLoad = (self.opcode == InstructionOpcodes.LOAD)      # rd <- mem[rs1 + Iimm]
        self.isStore = (self.opcode == InstructionOpcodes.STORE)    # mem[rs1 + Simm] <- rs2
        self.isBranch = (self.opcode == InstructionOpcodes.BRANCH)  # if (rs1 OP rs2) PC <- PC + Bimm
        self.isJal = (self.opcode == InstructionOpcodes.JAL)        # rd <- PC+4; PC <- rs1 + Jimm
        self.isJalr = (self.opcode == InstructionOpcodes.JALR)      # rd <- PC+4; PC <- Iimm
        self.isLUI = (self.opcode == InstructionOpcodes.LUI)        # rd <- Uimm
        self.isAUIPC = (self.opcode == InstructionOpcodes.AUIPC)    # rd <- PC + Uimm 
        self.isSystem = (self.opcode == InstructionOpcodes.SYSTEM)  # special

        sign = instruction[0]  # bit 31 = sign bit

        self.Iimm = sign * 21 + instruction[1:12] # inst[31:20] sign-extended to 32 bits
        self.Simm = sign * 21 + instruction[1:7] + instruction[20:25] # inst[31:25] + inst[11:7]
        self.Bimm = sign * 20 + instruction[24] + \
            instruction[1:7] + instruction[20:24] + \
            '0'                                   # inst[31] + inst[7] + inst[30:25] + inst[11:8] + 0
        self.Uimm = instruction[0:20] + '0' * 12  # inst[31:12] + 12 zeros
        self.Jimm = sign * 12 + \
            instruction[12:20] + instruction[11] + instruction[1:11] + \
            '0'                                   # inst[31] + inst[19:12] + inst[20] + inst[30:21] + 0


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
