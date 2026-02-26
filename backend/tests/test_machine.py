import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hymn.machine import MachineState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_machine(*words, origin=0):
    """Return a fresh MachineState with *words* loaded at *origin*."""
    m = MachineState()
    m.load_program(list(words), origin=origin)
    return m


def enc(opcode, address):
    return MachineState.encode(opcode, address)


H  = MachineState.HALT
J  = MachineState.JUMP
JZ = MachineState.JZER
JP = MachineState.JPOS
LD = MachineState.LOAD
ST = MachineState.STOR
AD = MachineState.ADD
SB = MachineState.SUB


# ===========================================================================
# 1. Reset / initial state
# ===========================================================================

class TestReset:

    def test_initial_registers_are_zero(self):
        m = MachineState()
        assert m.pc == 0 and m.ac == 0 and m.ir == 0

    def test_initial_memory_is_all_zeros(self):
        m = MachineState()
        assert all(m.read_memory(i) == 0 for i in range(MachineState.MEMORY_SIZE))

    def test_initial_not_halted(self):
        m = MachineState()
        assert m.halted == False

    def test_reset_clears_state_after_run(self):
        m = make_machine(enc(LD, 1), enc(H, 0), 42)
        m.run()
        m.reset()
        assert m.pc == 0 and m.ac == 0 and m.ir == 0 and m.halted == False
        assert all(m.read_memory(i) == 0 for i in range(MachineState.MEMORY_SIZE))


# ===========================================================================
# 2. HALT
# ===========================================================================

class TestHalt:

    def test_halt_at_address_zero_stops_immediately(self):
        m = MachineState()          # memory is all zeros → HALT at 0
        m.step()
        assert m.halted == True

    def test_halt_does_not_advance_pc(self):
        m = MachineState()
        m.step()
        assert m.pc == 0  # PC stays pointing at the HALT instruction

    def test_step_on_halted_machine_raises(self):
        m = MachineState()
        m.step()                    # executes HALT
        with pytest.raises(RuntimeError):
            m.step()                # must raise, not silently do nothing

    def test_run_on_halted_machine_raises(self):
        m = MachineState()
        m.run()                     # halts cleanly
        with pytest.raises(RuntimeError):
            m.run()


# ===========================================================================
# 3. JUMP
# ===========================================================================

class TestJump:

    def test_jump_sets_pc_to_address(self):
        m = make_machine(enc(J, 5))
        m.step()
        assert m.pc == 5

    def test_jump_to_self_is_infinite_loop(self):
        # JUMP 0 at address 0 — run() must not return on its own.
        # Use step() twice and verify PC stays at 0 both times.
        m = make_machine(enc(J, 0))
        m.step()
        assert m.pc == 0
        m.step()
        assert m.pc == 0


# ===========================================================================
# 4. JZER
# ===========================================================================

class TestJzer:

    def test_jzer_jumps_when_ac_is_zero(self):
        m = make_machine(enc(JZ, 10))
        # ac is already 0 after reset
        m.step()
        assert m.pc == 10

    def test_jzer_does_not_jump_when_ac_nonzero(self):
        m = make_machine(enc(JZ, 10))
        m.ac = 5
        m.step()
        assert m.pc == 1  # incremented, not jumped

    def test_jzer_does_not_jump_when_ac_negative(self):
        m = make_machine(enc(JZ, 10))
        m.ac = -3
        m.step()
        assert m.pc == 1


# ===========================================================================
# 5. JPOS
# ===========================================================================

class TestJpos:

    def test_jpos_jumps_when_ac_positive(self):
        m = make_machine(enc(JP, 10))
        m.ac = 1
        m.step()
        assert m.pc == 10

    def test_jpos_does_not_jump_when_ac_zero(self):
        # Zero is NOT positive — this is the easy-to-miss case.
        m = make_machine(enc(JP, 10))
        # ac == 0
        m.step()
        assert m.pc == 1

    def test_jpos_does_not_jump_when_ac_negative(self):
        m = make_machine(enc(JP, 10))
        m.ac = -1
        m.step()
        assert m.pc == 1


# ===========================================================================
# 6. LOAD
# ===========================================================================

class TestLoad:

    def test_load_reads_correct_memory_cell(self):
        # Memory layout: [LOAD 2, HALT, 42]
        m = make_machine(enc(LD, 2), enc(H, 0), 42)
        m.step()
        assert m.ac == 42

    def test_load_advances_pc(self):
        m = make_machine(enc(LD, 1), 0)
        m.step()
        assert m.pc == 1

    def test_load_zero_value(self):
        m = make_machine(enc(LD, 1), 0)
        m.step()
        assert m.ac == 0


# ===========================================================================
# 7. STOR
# ===========================================================================

class TestStor:

    def test_stor_writes_ac_to_memory(self):
        m = make_machine(enc(ST, 5))
        m.ac = 99
        m.step()
        assert m.read_memory(5) == 99

    def test_stor_advances_pc(self):
        m = make_machine(enc(ST, 5))
        m.step()
        assert m.pc == 1

    def test_stor_negative_ac_written_to_memory(self):
        # AC can be negative; the raw value ends up in memory.
        m = make_machine(enc(ST, 5))
        m.ac = -7
        m.step()
        assert m.read_memory(5) == -7


# ===========================================================================
# 8. ADD
# ===========================================================================

class TestAdd:

    def test_add_accumulates_correctly(self):
        # Memory: [ADD 2, HALT, 10]  with AC starting at 5
        m = make_machine(enc(AD, 2), enc(H, 0), 10)
        m.ac = 5
        m.step()
        assert m.ac == 15

    def test_add_advances_pc(self):
        m = make_machine(enc(AD, 1), 0)
        m.step()
        assert m.pc == 1

    def test_add_result_can_exceed_255(self):
        # HYMN AC is a plain Python int — there is no 8-bit wrapping.
        m = make_machine(enc(AD, 1), 200)
        m.ac = 200
        m.step()
        assert m.ac == 400  # not 144 / not an error


# ===========================================================================
# 9. SUB
# ===========================================================================

class TestSub:

    def test_sub_decrements_correctly(self):
        m = make_machine(enc(SB, 2), enc(H, 0), 3)
        m.ac = 10
        m.step()
        assert m.ac == 7

    def test_sub_result_can_be_negative(self):
        m = make_machine(enc(SB, 2), enc(H, 0), 10)
        m.ac = 3
        m.step()
        assert m.ac == -7

    def test_sub_advances_pc(self):
        m = make_machine(enc(SB, 1), 0)
        m.step()
        assert m.pc == 1


# ===========================================================================
# 10. PC boundary — the tricky overflow case
# ===========================================================================

class TestPCBoundary:

    def test_pc_at_31_after_non_halt_instruction(self):
        # Place a LOAD at address 31, data at address 0.
        # After the LOAD executes, PC becomes 32 — out of valid range.
        # The *next* step() should not silently succeed.
        m = MachineState()
        m.write_memory(31, enc(LD, 0))
        m.pc = 31
        m.step()                    # LOAD executes, PC → 32
        with pytest.raises((ValueError, IndexError)):
            m.step()                # must not silently access memory[32]


# ===========================================================================
# 11. load_program validation
# ===========================================================================

class TestLoadProgram:

    def test_program_fits_exactly(self):
        # 32 words starting at origin 0 should succeed without error.
        m = MachineState()
        m.load_program([0] * 32, origin=0)

    def test_program_overflows_raises(self):
        m = MachineState()
        with pytest.raises(ValueError):
            m.load_program([0] * 2, origin=31)  # needs addresses 31 & 32

    def test_empty_program_is_allowed(self):
        m = MachineState()
        m.load_program([])          # should not raise

    def test_program_at_nonzero_origin(self):
        m = MachineState()
        m.load_program([enc(H, 0)], origin=10)
        assert m.read_memory(10) == enc(H, 0)
        assert m.read_memory(0) == 0  # untouched


# ===========================================================================
# 12. encode / decode round-trip
# ===========================================================================

class TestEncodeDecode:

    def test_roundtrip_all_opcodes(self):
        for opcode in range(8):
            for address in [0, 15, 31]:
                word = MachineState.encode(opcode, address)
                op2, addr2 = MachineState.decode(word)
                assert op2 == opcode and addr2 == address

    def test_encode_rejects_bad_opcode(self):
        with pytest.raises(ValueError):
            MachineState.encode(8, 0)

    def test_encode_rejects_bad_address(self):
        with pytest.raises(ValueError):
            MachineState.encode(0, 32)

    def test_decode_masks_extra_bits(self):
        # Values > 255 still yield a valid opcode and address
        # because decode uses bit-masking.
        opcode, address = MachineState.decode(0xFF)
        assert 0 <= opcode <= 7
        assert 0 <= address <= 31


# ===========================================================================
# 13. snapshot
# ===========================================================================

class TestSnapshot:

    def test_snapshot_keys(self):
        m = MachineState()
        snap = m.snapshot()
        assert {"pc", "ac", "ir", "halted", "memory"} <= snap.keys()

    def test_snapshot_memory_is_copy(self):
        # Mutating the returned list must NOT affect the machine's memory.
        m = MachineState()
        snap = m.snapshot()
        snap["memory"][0] = 999
        assert m.read_memory(0) == 0
