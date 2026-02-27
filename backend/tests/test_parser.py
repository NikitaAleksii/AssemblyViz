import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hymn.parser import Parser, ParseError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def enc(opcode: int, operand: int = 0) -> int:
    """Encode a 3-bit opcode and 5-bit operand into one 8-bit word."""
    return (opcode << 5) | operand


# Opcode constants mirroring instructions.py
HALT = 0b000
JUMP = 0b001
JZER = 0b010
JPOS = 0b011
LOAD = 0b100
STOR = 0b101
ADD  = 0b110
SUB  = 0b111


# ===========================================================================
# 1. _tokenize_line
# ===========================================================================

class TestTokenizeLine:

    def setup_method(self):
        self.p = Parser()

    def test_blank_line_returns_empty(self):
        assert self.p._tokenize_line("") == []

    def test_whitespace_only_returns_empty(self):
        assert self.p._tokenize_line("   \t  ") == []

    def test_comment_only_returns_empty(self):
        assert self.p._tokenize_line("; this is a comment") == []

    def test_inline_comment_stripped(self):
        assert self.p._tokenize_line("ADD 5 ; add five") == ["ADD", "5"]

    def test_leading_whitespace_stripped(self):
        assert self.p._tokenize_line("   ADD 5") == ["ADD", "5"]

    def test_normalised_to_uppercase(self):
        assert self.p._tokenize_line("add 5") == ["ADD", "5"]

    def test_mixed_case_uppercased(self):
        assert self.p._tokenize_line("  Load 3 ") == ["LOAD", "3"]

    def test_label_with_instruction(self):
        assert self.p._tokenize_line("LOOP: ADD 5") == ["LOOP:", "ADD", "5"]

    def test_label_only_line(self):
        assert self.p._tokenize_line("START:") == ["START:"]

    def test_halt_no_operand(self):
        assert self.p._tokenize_line("HALT") == ["HALT"]

    def test_semicolon_at_start_is_full_comment(self):
        assert self.p._tokenize_line(";ADD 5") == []


# ===========================================================================
# 2. _is_label_definition
# ===========================================================================

class TestIsLabelDefinition:

    def setup_method(self):
        self.p = Parser()

    def test_simple_label_is_recognised(self):
        assert self.p._is_label_definition("LOOP:") is True

    def test_label_with_underscore(self):
        assert self.p._is_label_definition("MY_LABEL:") is True

    def test_mnemonic_is_not_a_label(self):
        assert self.p._is_label_definition("ADD") is False

    def test_numeric_token_is_not_a_label(self):
        assert self.p._is_label_definition("5") is False

    def test_token_starting_with_digit_is_not_a_label(self):
        assert self.p._is_label_definition("1LOOP:") is False

    def test_colon_only_is_not_a_label(self):
        assert self.p._is_label_definition(":") is False

    def test_empty_string_is_not_a_label(self):
        assert self.p._is_label_definition("") is False

    def test_label_without_colon_is_not_a_definition(self):
        # "LOOP" is a label reference, not a definition
        assert self.p._is_label_definition("LOOP") is False


# ===========================================================================
# 3. symbol_table — first pass
# ===========================================================================

class TestSymbolTable:

    def setup_method(self):
        self.p = Parser()

    def test_single_label_at_address_zero(self):
        self.p.parse("START:\nHALT")
        assert self.p.symbol_table["START"] == 0

    def test_label_after_instruction_gets_correct_address(self):
        src = "ADD 5\nLOOP:\nHALT"
        self.p.parse(src)
        assert self.p.symbol_table["LOOP"] == 1

    def test_multiple_labels(self):
        src = "START:\nADD 5\nEND:\nHALT"
        self.p.parse(src)
        assert self.p.symbol_table["START"] == 0
        assert self.p.symbol_table["END"] == 1

    def test_label_on_same_line_as_instruction(self):
        # LOOP: ADD 5 — label maps to the address of ADD
        src = "LOOP: ADD 5\nHALT"
        self.p.parse(src)
        assert self.p.symbol_table["LOOP"] == 0

    def test_label_only_line_does_not_advance_address(self):
        # START: on its own line should map to same address as the next instruction
        src = "START:\nHALT"
        self.p.parse(src)
        assert self.p.symbol_table["START"] == 0

    def test_blank_and_comment_lines_not_counted(self):
        src = "; comment\n\nHALT"
        self.p.parse(src)
        assert self.p.symbol_table == {}

    def test_symbol_table_reset_between_parses(self):
        self.p.parse("ALPHA:\nHALT")
        self.p.parse("BETA:\nHALT")
        assert "ALPHA" not in self.p.symbol_table
        assert "BETA" in self.p.symbol_table


# ===========================================================================
# 4. _resolve_operand
# ===========================================================================

class TestResolveOperand:

    def setup_method(self):
        self.p = Parser()
        self.p._symbolDict = {"LOOP": 3}

    def test_decimal_zero_is_valid(self):
        assert self.p._resolve_operand("0", 1) == 0

    def test_decimal_31_is_valid_boundary(self):
        assert self.p._resolve_operand("31", 1) == 31

    def test_decimal_32_is_out_of_range(self):
        result = self.p._resolve_operand("32", 1)
        assert result is None
        assert len(self.p._errorLst) == 1

    def test_label_reference_resolved(self):
        assert self.p._resolve_operand("LOOP", 1) == 3

    def test_undefined_label_returns_none_and_adds_error(self):
        result = self.p._resolve_operand("MISSING", 1)
        assert result is None
        assert len(self.p._errorLst) == 1

    def test_invalid_token_returns_none_and_adds_error(self):
        result = self.p._resolve_operand("@@@", 1)
        assert result is None
        assert len(self.p._errorLst) == 1

    def test_decimal_mid_range(self):
        assert self.p._resolve_operand("15", 1) == 15


# ===========================================================================
# 5. _encode_line
# ===========================================================================

class TestEncodeLine:

    def setup_method(self):
        self.p = Parser()

    def test_halt_encodes_correctly(self):
        assert self.p._encode_line(1, ["HALT"]) == enc(HALT)

    def test_add_encodes_correctly(self):
        assert self.p._encode_line(1, ["ADD", "5"]) == enc(ADD, 5)

    def test_jump_encodes_correctly(self):
        assert self.p._encode_line(1, ["JUMP", "10"]) == enc(JUMP, 10)

    def test_jzer_encodes_correctly(self):
        assert self.p._encode_line(1, ["JZER", "2"]) == enc(JZER, 2)

    def test_jpos_encodes_correctly(self):
        assert self.p._encode_line(1, ["JPOS", "7"]) == enc(JPOS, 7)

    def test_load_encodes_correctly(self):
        assert self.p._encode_line(1, ["LOAD", "3"]) == enc(LOAD, 3)

    def test_stor_encodes_correctly(self):
        assert self.p._encode_line(1, ["STOR", "4"]) == enc(STOR, 4)

    def test_sub_encodes_correctly(self):
        assert self.p._encode_line(1, ["SUB", "31"]) == enc(SUB, 31)

    def test_unknown_mnemonic_returns_none(self):
        result = self.p._encode_line(1, ["NOP"])
        assert result is None
        assert len(self.p._errorLst) == 1

    def test_halt_with_operand_returns_none(self):
        result = self.p._encode_line(1, ["HALT", "5"])
        assert result is None
        assert len(self.p._errorLst) == 1

    def test_add_with_no_operand_returns_none(self):
        result = self.p._encode_line(1, ["ADD"])
        assert result is None
        assert len(self.p._errorLst) == 1

    def test_add_with_two_operands_returns_none(self):
        result = self.p._encode_line(1, ["ADD", "1", "2"])
        assert result is None
        assert len(self.p._errorLst) == 1

    def test_operand_at_boundary_0(self):
        assert self.p._encode_line(1, ["LOAD", "0"]) == enc(LOAD, 0)

    def test_operand_at_boundary_31(self):
        assert self.p._encode_line(1, ["LOAD", "31"]) == enc(LOAD, 31)


# ===========================================================================
# 6. parse() — integration
# ===========================================================================

class TestParseIntegration:

    def setup_method(self):
        self.p = Parser()

    def test_empty_source_returns_empty_list(self):
        result = self.p.parse("")
        assert result == []

    def test_comment_only_returns_empty_list(self):
        result = self.p.parse("; just a comment\n; another")
        assert result == []

    def test_single_halt(self):
        assert self.p.parse("HALT") == [enc(HALT)]

    def test_multiple_instructions(self):
        src = "ADD 5\nHALT"
        assert self.p.parse(src) == [enc(ADD, 5), enc(HALT)]

    def test_label_forward_reference(self):
        # JMP to END which is defined on a later line
        src = "JUMP END\nHALT\nEND:\nHALT"
        result = self.p.parse(src)
        assert result is not None
        assert result[0] == enc(JUMP, 2)   # END is at address 2

    def test_label_backward_reference(self):
        # JMP back to LOOP defined earlier
        src = "LOOP:\nADD 5\nJUMP LOOP"
        result = self.p.parse(src)
        assert result is not None
        assert result[1] == enc(JUMP, 0)   # LOOP is at address 0

    def test_label_on_same_line_as_instruction(self):
        src = "LOOP: ADD 5\nHALT"
        result = self.p.parse(src)
        assert result == [enc(ADD, 5), enc(HALT)]

    def test_label_only_line_produces_no_word(self):
        src = "START:\nHALT"
        assert self.p.parse(src) == [enc(HALT)]

    def test_blank_lines_ignored(self):
        src = "ADD 5\n\n\nHALT"
        assert self.p.parse(src) == [enc(ADD, 5), enc(HALT)]

    def test_comment_lines_ignored(self):
        src = "; setup\nADD 5\n; done\nHALT"
        assert self.p.parse(src) == [enc(ADD, 5), enc(HALT)]

    def test_unknown_mnemonic_returns_none(self):
        assert self.p.parse("NOP") is None

    def test_undefined_label_returns_none(self):
        assert self.p.parse("JUMP NOWHERE") is None

    def test_operand_out_of_range_returns_none(self):
        assert self.p.parse("ADD 32") is None

    def test_errors_reset_between_calls(self):
        self.p.parse("NOP")          # produces an error
        assert len(self.p.errors) > 0
        self.p.parse("HALT")         # clean parse
        assert self.p.errors == []

    def test_successful_parse_has_no_errors(self):
        self.p.parse("HALT")
        assert self.p.errors == []

    def test_full_program_all_instructions(self):
        src = (
            "LOAD 10\n"
            "ADD 11\n"
            "STOR 12\n"
            "SUB 13\n"
            "JZER END\n"
            "JPOS END\n"
            "JUMP END\n"
            "END:\n"
            "HALT"
        )
        result = self.p.parse(src)
        assert result is not None
        assert len(result) == 8
        assert result[0] == enc(LOAD, 10)
        assert result[1] == enc(ADD,  11)
        assert result[2] == enc(STOR, 12)
        assert result[3] == enc(SUB,  13)
        assert result[4] == enc(JZER, 7)   # END is at address 7
        assert result[5] == enc(JPOS, 7)
        assert result[6] == enc(JUMP, 7)
        assert result[7] == enc(HALT)


# ===========================================================================
# 7. errors property
# ===========================================================================

class TestErrors:

    def setup_method(self):
        self.p = Parser()

    def test_errors_empty_after_successful_parse(self):
        self.p.parse("HALT")
        assert self.p.errors == []

    def test_errors_populated_on_bad_mnemonic(self):
        self.p.parse("NOP")
        assert len(self.p.errors) == 1
        assert isinstance(self.p.errors[0], ParseError)

    def test_error_contains_message(self):
        self.p.parse("NOP")
        assert "NOP" in self.p.errors[0].message

    def test_multiple_errors_accumulated(self):
        self.p.parse("NOP\nBAD\nADD 99")
        assert len(self.p.errors) >= 2

    def test_errors_cleared_on_next_parse(self):
        self.p.parse("NOP")
        self.p.parse("HALT")
        assert self.p.errors == []
