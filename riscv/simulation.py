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
            return a >> (b & 0b11111)  # logical right
        if mnemonic == "sra" or mnemonic == "srai":
            return a >> (b & 0b11111)  # arithmetic right
        if mnemonic == "slt" or mnemonic == "slti":
            return 1 if a < b else 0  # less than
        if mnemonic == "sltu" or mnemonic == "sltiu":
            # less than unsigned
            return 1 if (a & 0xFFFFFFFF) < (b & 0xFFFFFFFF) else 0

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

        alu_out = self._alu(instr_mnemonic, rs1,
                            (rs2 if self.isOPreg else Iimm))

        if instruction.isOPreg:
            self.registers.write(
                instruction.rd, alu_out)
            self.PC += 4
        if instruction.isOPimm:
            self.registers.write(
                instruction.rd, alu_out)
            self.PC += 4
        if instruction.isLoad:          # needs halfword anbd byte handling
            load_addr = rs1 + Iimm
            read_val = int(self.memory.memory_read(load_addr), 2)
            self.registers.write(
                instruction.rd, read_val
            )
            self.PC += 4
        if instruction.isStore:         # needs halfword anbd byte handling
            write_addr = rs1 + Simm
            read_val = int(self.memory.memory_read(load_addr), 2)
            self.memory.memory_write(write_addr, read_val, "1111")
            

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
