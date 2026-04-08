import unittest
from riscv.parser import Parser, ParsedLine, ParseError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_parser() -> Parser:
    return Parser()


# ===========================================================================
# 1. _tokenize_line
# ===========================================================================

class TestTokenizeLine(unittest.TestCase):

    def setUp(self):
        self.p = make_parser()

    def test_blank_line_returns_empty(self):
        self.assertEqual(self.p._tokenize_line(""), [])

    def test_whitespace_only_returns_empty(self):
        self.assertEqual(self.p._tokenize_line("   \t  "), [])

    def test_comment_only_returns_empty(self):
        self.assertEqual(self.p._tokenize_line("# this is a comment"), [])

    def test_inline_comment_stripped(self):
        self.assertEqual(self.p._tokenize_line("add x1, x2, x3 # comment"), ["add", "x1", "x2", "x3"])

    def test_commas_stripped(self):
        self.assertEqual(self.p._tokenize_line("addi x1, x2, 5"), ["addi", "x1", "x2", "5"])

    def test_leading_whitespace_stripped(self):
        self.assertEqual(self.p._tokenize_line("   add x1, x2, x3"), ["add", "x1", "x2", "x3"])

    def test_label_with_instruction(self):
        self.assertEqual(self.p._tokenize_line("loop: add x1, x2, x3"), ["loop:", "add", "x1", "x2", "x3"])

    def test_label_only_line(self):
        self.assertEqual(self.p._tokenize_line("start:"), ["start:"])

    def test_no_operand_instruction(self):
        self.assertEqual(self.p._tokenize_line("ecall"), ["ecall"])


# ===========================================================================
# 2. _split_lines
# ===========================================================================

class TestSplitLines(unittest.TestCase):

    def setUp(self):
        self.p = make_parser()

    def test_text_only(self):
        self.p._split_lines(["add x1, x2, x3", "ecall"])
        self.assertEqual(len(self.p._text_lines), 2)
        self.assertEqual(len(self.p._data_lines), 0)

    def test_data_only(self):
        self.p._split_lines([".data", ".word 1, 2, 3"])
        self.assertEqual(len(self.p._text_lines), 0)
        self.assertEqual(len(self.p._data_lines), 1)

    def test_text_then_data(self):
        self.p._split_lines(["add x1, x2, x3", ".data", ".word 1, 2, 3"])
        self.assertEqual(len(self.p._text_lines), 1)
        self.assertEqual(len(self.p._data_lines), 1)

    def test_data_then_text(self):
        self.p._split_lines([".data", ".word 1", ".text", "add x1, x2, x3"])
        self.assertEqual(len(self.p._text_lines), 1)
        self.assertEqual(len(self.p._data_lines), 1)

    def test_blank_lines_ignored(self):
        self.p._split_lines(["", "add x1, x2, x3", ""])
        self.assertEqual(len(self.p._text_lines), 1)

    def test_comment_lines_ignored(self):
        self.p._split_lines(["# comment", "add x1, x2, x3"])
        self.assertEqual(len(self.p._text_lines), 1)


# ===========================================================================
# 3. symbol_table — first pass
# ===========================================================================

class TestSymbolTable(unittest.TestCase):

    def setUp(self):
        self.p = make_parser()

    def test_single_label_at_address_zero(self):
        self.p.parse("main:\n    ecall")
        self.assertEqual(self.p.symbol_table["main"], 0)

    def test_label_after_instruction(self):
        self.p.parse("add x1, x2, x3\nloop:\n    ecall")
        self.assertEqual(self.p.symbol_table["loop"], 4)

    def test_multiple_labels(self):
        self.p.parse("start:\n    add x1, x2, x3\nend:\n    ecall")
        self.assertEqual(self.p.symbol_table["start"], 0)
        self.assertEqual(self.p.symbol_table["end"], 4)

    def test_label_on_same_line_as_instruction(self):
        self.p.parse("loop: add x1, x2, x3\necall")
        self.assertEqual(self.p.symbol_table["loop"], 0)

    def test_label_only_line_does_not_advance_address(self):
        self.p.parse("start:\n    ecall")
        self.assertEqual(self.p.symbol_table["start"], 0)

    def test_data_label_after_text(self):
        src = "add x1, x2, x3\n.data\narray: .word 1 2 3"
        self.p.parse(src)
        self.assertEqual(self.p.symbol_table["array"], 4)

    def test_symbol_table_reset_between_parses(self):
        self.p.parse("alpha:\n    ecall")
        self.p.parse("beta:\n    ecall")
        self.assertNotIn("alpha", self.p.symbol_table)
        self.assertIn("beta", self.p.symbol_table)

    def test_duplicate_label_produces_error(self):
        self.p.parse("loop:\n    add x1, x2, x3\nloop:\n    ecall")
        self.assertGreater(len(self.p.errors), 0)

    def test_reserved_label_produces_error(self):
        self.p.parse("add:\n    ecall")
        self.assertGreater(len(self.p.errors), 0)

    def test_register_name_as_label_produces_error(self):
        self.p.parse("x1:\n    ecall")
        self.assertGreater(len(self.p.errors), 0)

    def test_la_counts_as_two_instructions(self):
        self.p.parse("la x1, label\nloop:\n    ecall\nlabel:")
        self.assertEqual(self.p.symbol_table["loop"], 8)


# ===========================================================================
# 4. parse() — second pass text lines
# ===========================================================================

class TestParseTextLines(unittest.TestCase):

    def setUp(self):
        self.p = make_parser()

    def test_empty_source_returns_empty_list(self):
        result = self.p.parse("")
        self.assertEqual(result, [])

    def test_comment_only_returns_empty_list(self):
        result = self.p.parse("# just a comment")
        self.assertEqual(result, [])

    def test_single_instruction(self):
        result = self.p.parse("ecall")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].mnemonic, "ecall")
        self.assertEqual(result[0].operands, [])

    def test_label_stripped_from_parsed_line(self):
        result = self.p.parse("main:\n    ecall")
        self.assertIsNotNone(result)
        self.assertEqual(result[0].label, "main")
        self.assertEqual(result[0].mnemonic, "ecall")

    def test_label_only_line_produces_no_parsed_line(self):
        result = self.p.parse("main:\n    ecall")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)

    def test_r_type_instruction(self):
        result = self.p.parse("add x1, x2, x3")
        self.assertIsNotNone(result)
        self.assertEqual(result[0].mnemonic, "add")
        self.assertEqual(result[0].operands, ["x1", "x2", "x3"])

    def test_i_type_instruction(self):
        result = self.p.parse("addi x1, x2, 5")
        self.assertIsNotNone(result)
        self.assertEqual(result[0].mnemonic, "addi")
        self.assertEqual(result[0].operands, ["x1", "x2", "5"])

    def test_load_instruction(self):
        result = self.p.parse("lw x1, 8(x2)")
        self.assertIsNotNone(result)
        self.assertEqual(result[0].mnemonic, "lw")
        self.assertEqual(result[0].operands, ["x1", "8(x2)"])

    def test_store_instruction(self):
        result = self.p.parse("sw x1, 8(x2)")
        self.assertIsNotNone(result)
        self.assertEqual(result[0].mnemonic, "sw")
        self.assertEqual(result[0].operands, ["x1", "8(x2)"])

    def test_branch_instruction_with_label(self):
        result = self.p.parse("main:\n    beq x1, x2, main")
        self.assertIsNotNone(result)
        self.assertEqual(result[0].mnemonic, "beq")
        self.assertEqual(result[0].operands, ["x1", "x2", "main"])

    def test_unknown_mnemonic_returns_none(self):
        result = self.p.parse("foo x1, x2, x3")
        self.assertIsNone(result)
        self.assertEqual(len(self.p.errors), 1)

    def test_errors_reset_between_parses(self):
        self.p.parse("foo x1, x2, x3")
        self.assertGreater(len(self.p.errors), 0)
        self.p.parse("ecall")
        self.assertEqual(self.p.errors, [])

    def test_successful_parse_has_no_errors(self):
        self.p.parse("ecall")
        self.assertEqual(self.p.errors, [])

    def test_multiple_instructions(self):
        src = "add x1, x2, x3\naddi x1, x1, 1\necall"
        result = self.p.parse(src)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)

    def test_label_inline_with_instruction(self):
        result = self.p.parse("loop: add x1, x2, x3")
        self.assertIsNotNone(result)
        self.assertEqual(result[0].label, "loop")
        self.assertEqual(result[0].mnemonic, "add")


# ===========================================================================
# 5. parse() — second pass data lines
# ===========================================================================

class TestParseDataLines(unittest.TestCase):

    def setUp(self):
        self.p = make_parser()

    def test_word_directive(self):
        result = self.p.parse(".data\n.word 1 2 3")
        self.assertIsNotNone(result)
        self.assertEqual(result[0].mnemonic, ".word")
        self.assertEqual(result[0].data_words, [1, 2, 3])

    def test_asciz_directive(self):
        result = self.p.parse('.data\n.asciz "hi"')
        self.assertIsNotNone(result)
        self.assertEqual(result[0].mnemonic, ".asciz")
        self.assertIsNotNone(result[0].data_words)

    def test_data_label_stored(self):
        result = self.p.parse(".data\narray: .word 1 2 3")
        self.assertIsNotNone(result)
        self.assertEqual(result[0].label, "array")

    def test_unknown_directive_returns_none(self):
        result = self.p.parse(".data\n.foo 1 2 3")
        self.assertIsNone(result)
        self.assertEqual(len(self.p.errors), 1)

    def test_data_words_stored_on_parsed_line(self):
        result = self.p.parse(".data\n.word 10 20 30")
        self.assertIsNotNone(result)
        self.assertEqual(result[0].data_words, [10, 20, 30])


# ===========================================================================
# 6. operand validation
# ===========================================================================

class TestOperandValidation(unittest.TestCase):

    def setUp(self):
        self.p = make_parser()

    def test_invalid_register_returns_none(self):
        result = self.p.parse("add x99, x2, x3")
        self.assertIsNone(result)

    def test_invalid_immediate_returns_none(self):
        result = self.p.parse("addi x1, x2, abc")
        self.assertIsNone(result)

    def test_invalid_memory_operand_returns_none(self):
        result = self.p.parse("lw x1, x2")
        self.assertIsNone(result)

    def test_undefined_label_returns_none(self):
        result = self.p.parse("beq x1, x2, nowhere")
        self.assertIsNone(result)

    def test_wrong_operand_count_r_type(self):
        result = self.p.parse("add x1, x2")
        self.assertIsNone(result)

    def test_wrong_operand_count_i_type(self):
        result = self.p.parse("addi x1, x2")
        self.assertIsNone(result)

    def test_no_operand_instruction_with_operands(self):
        result = self.p.parse("ecall x1")
        self.assertIsNone(result)

    def test_hex_immediate_valid(self):
        result = self.p.parse("addi x1, x2, 0xFF")
        self.assertIsNotNone(result)

    def test_negative_immediate_valid(self):
        result = self.p.parse("addi x1, x2, -5")
        self.assertIsNotNone(result)

    def test_abi_register_names_valid(self):
        result = self.p.parse("add a0, a1, a2")
        self.assertIsNotNone(result)


# ===========================================================================
# 7. errors property
# ===========================================================================

class TestErrors(unittest.TestCase):

    def setUp(self):
        self.p = make_parser()

    def test_errors_empty_after_successful_parse(self):
        self.p.parse("ecall")
        self.assertEqual(self.p.errors, [])

    def test_errors_populated_on_bad_mnemonic(self):
        self.p.parse("foo x1, x2, x3")
        self.assertEqual(len(self.p.errors), 1)
        self.assertIsInstance(self.p.errors[0], ParseError)

    def test_error_contains_message(self):
        self.p.parse("foo x1, x2, x3")
        self.assertIn("foo", self.p.errors[0].message)

    def test_multiple_errors_accumulated(self):
        self.p.parse("foo x1, x2, x3\nbar x1, x2, x3")
        self.assertGreaterEqual(len(self.p.errors), 2)

    def test_errors_cleared_on_next_parse(self):
        self.p.parse("foo x1, x2, x3")
        self.p.parse("ecall")
        self.assertEqual(self.p.errors, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)