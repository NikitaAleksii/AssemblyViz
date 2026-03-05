from riscv.isa import *
from riscv.assembler import *
from riscv.decoder import *
from riscv.memory import *
from riscv.registers import *


class Simulation:
    def _alu(self, mnemonic, a, b) -> int:
        if mnemonic == "add" or mnemonic == "addi":
            return a + b
        if mnemonic == "sub":
            return a - b
        if mnemonic == "and" or mnemonic == "andi":
            return a & b
        if mnemonic == "or" or mnemonic == "ori":
            return a | b
        if mnemonic == "xor" or mnemonic == "xori":
            return a ^ b
        if mnemonic == "sll" or mnemonic == "slli":
            return a << (b & 0b11111)  # logical left
        if mnemonic == "srl" or mnemonic == "srli":
            return (a & 0xFFFFFFFF) >> (b & 0b11111)   # logical right
        if mnemonic == "sra" or mnemonic == "srai":
            return to_signed(a, 32) >> (b & 0b11111)   # arithmetic right
        if mnemonic == "slt" or mnemonic == "slti":
            return 1 if a < b else 0  # less than
        if mnemonic == "sltu" or mnemonic == "sltiu":
            # less than unsigned
            return 1 if (a & 0xFFFFFFFF) < (b & 0xFFFFFFFF) else 0
        
        return 0

    def __init__(self, memory_depth=256):
        self.memory_depth = memory_depth
        self.memory = Memory(self.memory_depth, "")
        self.registers = Registers()
        self.PC = 0
        self.halted = False

    def load(self, source: str):
        words = assemble(source)
        for i, word in enumerate(words):
            self.memory.memory_write(i * 4, word, "1111")
        self.PC = 0
        self.halted = False

    def step(self):
        if self.halted:
            return self.snapshot()

        word = int(self.memory.memory_read(self.PC), 2)
        instruction = DecodedInstruction(word)
        self._execute(instruction)

        return self.snapshot()

    def reset(self):
        self.memory = Memory(self.memory_depth, "")
        self.registers = Registers()
        self.PC = 0
        self.halted = False

    def _execute(self, instruction):
        instr_mnemonic = (MNEMONICS.get((instruction.opcode, instruction.funct3, instruction.funct7)) or
                          MNEMONICS.get((instruction.opcode, instruction.funct3)) or
                          MNEMONICS.get((instruction.opcode, None))
                          )

        rs1 = self.registers.read(instruction.rs1)
        rs2 = self.registers.read(instruction.rs2)

        Iimm = instruction.Iimm
        Simm = instruction.Simm
        Bimm = instruction.Bimm
        Jimm = instruction.Jimm
        Uimm = instruction.Uimm

        alu_out = self._alu(instr_mnemonic, rs1,
                            (rs2 if instruction.isOPreg else Iimm))

        # Handle R-type instructions
        if instruction.isOPreg:
            self.registers.write(
                instruction.rd, alu_out)
            self.PC += 4

        # Handle I-type ALU instructions
        elif instruction.isOPimm:
            self.registers.write(
                instruction.rd, alu_out)
            self.PC += 4

        # Handle Load
        elif instruction.isLoad:    
            load_addr = rs1 + Iimm
            word_addr = load_addr & ~0b11
            read_val = int(self.memory.memory_read(word_addr), 2)

            if instr_mnemonic == "lw":
                result = read_val

            elif instr_mnemonic in ("lh", "lhu"):
                # bit 1 of address selects which halfword
                if load_addr & 0b10:
                    # select upper halfword
                    halfword = (read_val >> 16) & 0xFFFF
                else:
                    halfword = read_val & 0xFFFF         # select lower halfword

                result = to_signed(
                    halfword, 16) if instr_mnemonic == "lh" else halfword

            elif instr_mnemonic in ("lb", "lbu"):
                # bits [1:0] select which byte
                byte_select = load_addr & 0b11
                if byte_select == 0:
                    byte = read_val & 0xFF
                elif byte_select == 1:
                    byte = (read_val >> 8) & 0xFF
                elif byte_select == 2:
                    byte = (read_val >> 16) & 0xFF
                else:
                    byte = (read_val >> 24) & 0xFF

                result = to_signed(
                    byte, 8) if instr_mnemonic == "lb" else byte
            else:
                result = 0
                
            self.registers.write(
                instruction.rd, result
            )
            self.PC += 4

        # Handle Store
        elif instruction.isStore:  
            write_addr = rs1 + Simm
            word_write = write_addr & ~0b11

            if instr_mnemonic == "sw":
                self.memory.memory_write(word_write, rs2, "1111")

            elif instr_mnemonic == "sh":
                # bit 1 selects which halfword lane
                if write_addr & 0b10:
                    # store upper halfword
                    self.memory.memory_write(word_write, rs2 << 16, "1100")
                else:
                    # store lower halfword
                    self.memory.memory_write(word_write, rs2, "0011")

            elif instr_mnemonic == "sb":
                byte_select = write_addr & 0x3
                if byte_select == 0:
                    self.memory.memory_write(word_write, rs2, "0001")
                elif byte_select == 1:
                    self.memory.memory_write(word_write, rs2 << 8, "0010")
                elif byte_select == 2:
                    self.memory.memory_write(word_write, rs2 << 16, "0100")
                else:
                    self.memory.memory_write(word_write, rs2 << 24, "1000")

            self.PC += 4

            # Handle Branches
        elif instruction.isBranch:
            takeBranch = False

            if instr_mnemonic == "beq" and rs1 == rs2:
                takeBranch = True
            elif instr_mnemonic == "bne" and rs1 != rs2:
                takeBranch = True
            elif instr_mnemonic == "blt" and rs1 < rs2:
                takeBranch = True
            elif instr_mnemonic == "bge" and rs1 >= rs2:
                takeBranch = True
            elif instr_mnemonic == "bltu" and (rs1 & 0xFFFFFFFF) < (rs2 & 0xFFFFFFFF):
                takeBranch = True
            elif instr_mnemonic == "bgeu" and (rs1 & 0xFFFFFFFF) >= (rs2 & 0xFFFFFFFF):
                takeBranch = True

            if takeBranch:
                self.PC += Bimm
            else:
                self.PC += 4

        # Handle Jump and Link (JAL)
        elif instruction.isJal:
            self.registers.write(
                instruction.rd, self.PC + 4
            )
            self.PC += Jimm

        # Handle Jump and Link Register (JALR)
        elif instruction.isJalr:
            self.registers.write(
                instruction.rd, self.PC + 4
            )
            self.PC = rs1 + Iimm

        # Handle Load Upper Immediate (LUI)
        elif instruction.isLUI:
            self.registers.write(
                instruction.rd, Uimm << 12
            )
            self.PC += 4

        # Handle Add Upper Immediate to PC (AUIPC)
        elif instruction.isAUIPC:
            self.registers.write(
                instruction.rd, self.PC + (Uimm << 12)
            )
            self.PC += 4

        # Handle System calls
        elif instruction.isSystem:
            self.halted = True

    def snapshot(self):
        return {
            "PC": self.PC,
            "halted": self.halted,
            "registers": [
                {"index": i,
                 "names": REGISTER_NAMES[i],
                 "value": self.registers.read(i)}
                for i in range(32)
            ],
            "memory": self.memory.memory
        }