import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hymn.instructions import INSTRUCTIONS, INSTRUCTIONS_BY_OPCODE, InstructionDef, OperandType


ALL_MNEMONICS = {"HALT", "JUMP", "JZER", "JPOS", "LOAD", "STOR", "ADD", "SUB"}
ALL_OPCODES   = {0b000, 0b001, 0b010, 0b011, 0b100, 0b101, 0b110, 0b111}


# ===========================================================================
# 1. Registry completeness
# ===========================================================================

class TestRegistryCompleteness:

    def test_all_mnemonics_registered(self):
        assert set(INSTRUCTIONS.keys()) == ALL_MNEMONICS

    def test_all_opcodes_registered(self):
        assert set(INSTRUCTIONS_BY_OPCODE.keys()) == ALL_OPCODES

    def test_no_duplicate_opcodes(self):
        # If two instructions share an opcode, one silently overwrites the other
        # and the two dicts end up with different lengths.
        assert len(INSTRUCTIONS) == len(INSTRUCTIONS_BY_OPCODE)


# ===========================================================================
# 2. Opcode range
# ===========================================================================

class TestOpcodeRange:

    def test_all_opcodes_in_3bit_range(self):
        for defn in INSTRUCTIONS.values():
            assert 0 <= defn.opcode <= 7, f"{defn.mnemonic} opcode out of range: {defn.opcode}"


# ===========================================================================
# 3. Per-instruction correctness
# ===========================================================================

class TestInstructionDetails:

    @pytest.mark.parametrize("mnemonic, expected_opcode, expected_operand_count", [
        ("HALT", 0b000, 0),
        ("JUMP", 0b001, 1),
        ("JZER", 0b010, 1),
        ("JPOS", 0b011, 1),
        ("LOAD", 0b100, 1),
        ("STOR", 0b101, 1),
        ("ADD",  0b110, 1),
        ("SUB",  0b111, 1),
    ])
    def test_opcode_and_operand_count(self, mnemonic, expected_opcode, expected_operand_count):
        defn = INSTRUCTIONS[mnemonic]
        assert defn.opcode == expected_opcode
        assert defn.operand_count == expected_operand_count

    @pytest.mark.parametrize("mnemonic", ["JUMP", "JZER", "JPOS", "LOAD", "STOR", "ADD", "SUB"])
    def test_single_operand_is_address_type(self, mnemonic):
        assert INSTRUCTIONS[mnemonic].operands[0] == OperandType.ADDRESS

    def test_halt_has_no_operands(self):
        assert INSTRUCTIONS["HALT"].operands == ()


# ===========================================================================
# 4. Companion index consistency
# ===========================================================================

class TestCompanionIndex:

    def test_roundtrip_mnemonic_to_opcode_to_mnemonic(self):
        for mnemonic, defn in INSTRUCTIONS.items():
            looked_up = INSTRUCTIONS_BY_OPCODE[defn.opcode]
            assert looked_up.mnemonic == mnemonic

    def test_roundtrip_opcode_to_mnemonic_to_opcode(self):
        for opcode, defn in INSTRUCTIONS_BY_OPCODE.items():
            looked_up = INSTRUCTIONS[defn.mnemonic]
            assert looked_up.opcode == opcode


# ===========================================================================
# 5. Immutability
# ===========================================================================

class TestImmutability:

    def test_instruction_def_is_frozen(self):
        defn = INSTRUCTIONS["ADD"]
        with pytest.raises(Exception):   # FrozenInstanceError is a subclass of AttributeError
            defn.opcode = 99
