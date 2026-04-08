import unittest
from riscv.parser import Parser
from riscv.assembler import Assembler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def assemble(source: str) -> list[int]:
    parser = Parser()
    parsed_lines = parser.parse(source)
    assembler = Assembler()
    return assembler.assemble(parsed_lines, parser.symbol_table)


def field(word: int, hi: int, lo: int) -> int:
    """Extract a bit field from a 32-bit word."""
    mask = (1 << (hi - lo + 1)) - 1
    return (word >> lo) & mask


# ===========================================================================
# 1. R-Type
# ===========================================================================

class TestRType(unittest.TestCase):

    def test_add(self):
        w = assemble("add x1, x2, x3")[0]
        self.assertEqual(field(w, 31, 25), 0b0000000)  # funct7
        self.assertEqual(field(w, 24, 20), 3)           # rs2 = x3
        self.assertEqual(field(w, 19, 15), 2)           # rs1 = x2
        self.assertEqual(field(w, 14, 12), 0b000)       # funct3
        self.assertEqual(field(w, 11,  7), 1)           # rd  = x1
        self.assertEqual(field(w,  6,  0), 0b0110011)   # opcode

    def test_sub(self):
        w = assemble("sub x1, x2, x3")[0]
        self.assertEqual(field(w, 31, 25), 0b0100000)
        self.assertEqual(field(w, 14, 12), 0b000)
        self.assertEqual(field(w,  6,  0), 0b0110011)

    def test_and(self):
        w = assemble("and x4, x5, x6")[0]
        self.assertEqual(field(w, 14, 12), 0b111)
        self.assertEqual(field(w, 24, 20), 6)
        self.assertEqual(field(w, 19, 15), 5)
        self.assertEqual(field(w, 11,  7), 4)

    def test_or(self):
        w = assemble("or x4, x5, x6")[0]
        self.assertEqual(field(w, 14, 12), 0b110)

    def test_xor(self):
        w = assemble("xor x4, x5, x6")[0]
        self.assertEqual(field(w, 14, 12), 0b100)

    def test_sll(self):
        w = assemble("sll x1, x2, x3")[0]
        self.assertEqual(field(w, 14, 12), 0b001)

    def test_srl(self):
        w = assemble("srl x1, x2, x3")[0]
        self.assertEqual(field(w, 31, 25), 0b0000000)
        self.assertEqual(field(w, 14, 12), 0b101)

    def test_sra(self):
        w = assemble("sra x1, x2, x3")[0]
        self.assertEqual(field(w, 31, 25), 0b0100000)
        self.assertEqual(field(w, 14, 12), 0b101)

    def test_slt(self):
        w = assemble("slt x1, x2, x3")[0]
        self.assertEqual(field(w, 14, 12), 0b010)
        self.assertEqual(field(w,  6,  0), 0b0110011)

    def test_sltu(self):
        w = assemble("sltu x1, x2, x3")[0]
        self.assertEqual(field(w, 14, 12), 0b011)
        self.assertEqual(field(w,  6,  0), 0b0110011)


# ===========================================================================
# 2. I-Type ALU
# ===========================================================================

class TestITypeALU(unittest.TestCase):

    def test_addi_positive(self):
        w = assemble("addi x1, x2, 10")[0]
        self.assertEqual(field(w, 31, 20), 10)
        self.assertEqual(field(w, 19, 15), 2)
        self.assertEqual(field(w, 14, 12), 0b000)
        self.assertEqual(field(w, 11,  7), 1)
        self.assertEqual(field(w,  6,  0), 0b0010011)

    def test_addi_negative(self):
        w = assemble("addi x1, x2, -5")[0]
        self.assertEqual(field(w, 31, 20), 0xFFB)

    def test_addi_zero_is_nop(self):
        w = assemble("addi x0, x0, 0")[0]
        self.assertEqual(w, 0b00000000000000000000000000010011)

    def test_andi(self):
        w = assemble("andi x1, x2, 15")[0]
        self.assertEqual(field(w, 14, 12), 0b111)
        self.assertEqual(field(w, 31, 20), 15)

    def test_ori(self):
        w = assemble("ori x1, x2, 7")[0]
        self.assertEqual(field(w, 14, 12), 0b110)

    def test_xori(self):
        w = assemble("xori x1, x2, 1")[0]
        self.assertEqual(field(w, 14, 12), 0b100)

    def test_slli(self):
        w = assemble("slli x1, x2, 4")[0]
        self.assertEqual(field(w, 14, 12), 0b001)
        self.assertEqual(field(w, 24, 20), 4)

    def test_srli(self):
        w = assemble("srli x1, x2, 4")[0]
        self.assertEqual(field(w, 31, 25), 0b0000000)
        self.assertEqual(field(w, 14, 12), 0b101)

    def test_srai(self):
        w = assemble("srai x1, x2, 4")[0]
        self.assertEqual(field(w, 31, 25), 0b0100000)
        self.assertEqual(field(w, 14, 12), 0b101)

    def test_slti(self):
        w = assemble("slti x1, x2, 5")[0]
        self.assertEqual(field(w, 14, 12), 0b010)
        self.assertEqual(field(w,  6,  0), 0b0010011)

    def test_sltiu(self):
        w = assemble("sltiu x1, x2, 5")[0]
        self.assertEqual(field(w, 14, 12), 0b011)
        self.assertEqual(field(w,  6,  0), 0b0010011)


# ===========================================================================
# 3. Load and Store
# ===========================================================================

class TestLoadStore(unittest.TestCase):

    def test_lw(self):
        w = assemble("lw x1, 8(x2)")[0]
        self.assertEqual(field(w, 31, 20), 8)
        self.assertEqual(field(w, 19, 15), 2)
        self.assertEqual(field(w, 14, 12), 0b010)
        self.assertEqual(field(w, 11,  7), 1)
        self.assertEqual(field(w,  6,  0), 0b0000011)

    def test_lw_negative_offset(self):
        w = assemble("lw x1, -4(x2)")[0]
        self.assertEqual(field(w, 31, 20), 0xFFC)

    def test_lb(self):
        self.assertEqual(field(assemble("lb x1, 0(x2)")[0], 14, 12), 0b000)

    def test_lh(self):
        self.assertEqual(field(assemble("lh x1, 0(x2)")[0], 14, 12), 0b001)

    def test_lbu(self):
        self.assertEqual(field(assemble("lbu x1, 0(x2)")[0], 14, 12), 0b100)

    def test_lhu(self):
        self.assertEqual(field(assemble("lhu x1, 0(x2)")[0], 14, 12), 0b101)

    def test_sw(self):
        w = assemble("sw x2, 8(x1)")[0]
        imm = (field(w, 31, 25) << 5) | field(w, 11, 7)
        self.assertEqual(imm, 8)
        self.assertEqual(field(w, 24, 20), 2)
        self.assertEqual(field(w, 19, 15), 1)
        self.assertEqual(field(w,  6,  0), 0b0100011)

    def test_sb(self):
        w = assemble("sb x2, 0(x1)")[0]
        self.assertEqual(field(w, 14, 12), 0b000)
        self.assertEqual(field(w,  6,  0), 0b0100011)

    def test_sh(self):
        self.assertEqual(field(assemble("sh x2, 0(x1)")[0], 14, 12), 0b001)


# ===========================================================================
# 4. Branch
# ===========================================================================

class TestBranch(unittest.TestCase):

    def test_beq(self):
        w = assemble("beq x1, x2, 4")[0]
        self.assertEqual(field(w,  6,  0), 0b1100011)
        self.assertEqual(field(w, 14, 12), 0b000)

    def test_bne(self):
        self.assertEqual(field(assemble("bne x1, x2, 4")[0], 14, 12), 0b001)

    def test_blt(self):
        self.assertEqual(field(assemble("blt x1, x2, 4")[0], 14, 12), 0b100)

    def test_bge(self):
        self.assertEqual(field(assemble("bge x1, x2, 4")[0], 14, 12), 0b101)

    def test_bltu(self):
        self.assertEqual(field(assemble("bltu x1, x2, 4")[0], 14, 12), 0b110)

    def test_bgeu(self):
        self.assertEqual(field(assemble("bgeu x1, x2, 4")[0], 14, 12), 0b111)

    def test_branch_with_label(self):
        src = "main:\n    add x1, x2, x3\n    beq x1, x2, main"
        w = assemble(src)[1]
        self.assertEqual(field(w,  6,  0), 0b1100011)


# ===========================================================================
# 5. U-Type
# ===========================================================================

class TestUType(unittest.TestCase):

    def test_lui(self):
        w = assemble("lui x1, 1")[0]
        self.assertEqual(field(w, 31, 12), 1)
        self.assertEqual(field(w, 11,  7), 1)
        self.assertEqual(field(w,  6,  0), 0b0110111)

    def test_auipc(self):
        w = assemble("auipc x1, 1")[0]
        self.assertEqual(field(w, 31, 12), 1)
        self.assertEqual(field(w,  6,  0), 0b0010111)


# ===========================================================================
# 6. Jumps
# ===========================================================================

class TestJumps(unittest.TestCase):

    def test_jal(self):
        w = assemble("jal x1, 4")[0]
        self.assertEqual(field(w, 11,  7), 1)
        self.assertEqual(field(w,  6,  0), 0b1101111)

    def test_jalr(self):
        w = assemble("jalr x1, x2, 0")[0]
        self.assertEqual(field(w, 19, 15), 2)
        self.assertEqual(field(w, 14, 12), 0b000)
        self.assertEqual(field(w, 11,  7), 1)
        self.assertEqual(field(w,  6,  0), 0b1100111)

    def test_jal_with_label(self):
        src = "jal x1, target\ntarget:\n    ecall"
        w = assemble(src)[0]
        self.assertEqual(field(w,  6,  0), 0b1101111)


# ===========================================================================
# 7. System
# ===========================================================================

class TestSystem(unittest.TestCase):

    def test_ecall(self):
        self.assertEqual(assemble("ecall")[0], 0b00000000000000000000000001110011)

    def test_ebreak(self):
        self.assertEqual(assemble("ebreak")[0], 0b00000000000100000000000001110011)


# ===========================================================================
# 8. Pseudo-ops
# ===========================================================================

class TestPseudoOps(unittest.TestCase):

    def test_mv(self):
        w = assemble("mv x1, x2")[0]
        self.assertEqual(field(w,  6,  0), 0b0010011)  # addi opcode
        self.assertEqual(field(w, 19, 15), 2)           # rs1 = x2
        self.assertEqual(field(w, 11,  7), 1)           # rd  = x1
        self.assertEqual(field(w, 31, 20), 0)           # imm = 0

    def test_nop(self):
        w = assemble("nop")[0]
        self.assertEqual(w, 0b00000000000000000000000000010011)

    def test_ret(self):
        w = assemble("ret")[0]
        self.assertEqual(field(w,  6,  0), 0b1100111)  # jalr opcode

    def test_j(self):
        w = assemble("j 4")[0]
        self.assertEqual(field(w,  6,  0), 0b1101111)  # jal opcode
        self.assertEqual(field(w, 11,  7), 0)           # rd = x0

    def test_li_small(self):
        words = assemble("li x1, 5")
        self.assertEqual(len(words), 1)
        self.assertEqual(field(words[0],  6,  0), 0b0010011)

    def test_li_large(self):
        words = assemble("li x1, 4096")
        self.assertEqual(len(words), 2)

    def test_la(self):
        src = "la x1, label\nlabel:\n    ecall"
        words = assemble(src)
        self.assertEqual(len(words), 3)  # lui + addi + ecall


# ===========================================================================
# 9. Multi-instruction
# ===========================================================================

class TestMultiInstruction(unittest.TestCase):

    def test_multiple_instructions_length(self):
        source = "add x1, x2, x3\naddi x4, x4, 1\nsw x1, 0(x2)\nlw x3, 0(x2)"
        self.assertEqual(len(assemble(source)), 4)

    def test_comments_ignored(self):
        source = "add x1, x2, x3  # comment\n# full line comment\naddi x4, x4, 1"
        self.assertEqual(len(assemble(source)), 2)

    def test_empty_lines_ignored(self):
        self.assertEqual(len(assemble("\nadd x1, x2, x3\n\naddi x4, x4, 1\n")), 2)

    def test_each_word_is_32_bits(self):
        source = "add x1, x2, x3\naddi x4, x5, 100\nlw x6, 4(x7)"
        for word in assemble(source):
            self.assertLessEqual(word, 0xFFFFFFFF)
            self.assertGreaterEqual(word, 0)

    def test_data_section_after_text(self):
        src = "lw x1, 0(x2)\n.data\n.word 42"
        words = assemble(src)
        self.assertEqual(len(words), 2)  # one instruction + one data word
        self.assertEqual(words[1], 42)

    def test_abi_register_names(self):
        w = assemble("add a0, a1, a2")[0]
        self.assertEqual(field(w, 11,  7), 10)   # a0 = x10
        self.assertEqual(field(w, 19, 15), 11)   # a1 = x11
        self.assertEqual(field(w, 24, 20), 12)   # a2 = x12


if __name__ == "__main__":
    unittest.main(verbosity=2)