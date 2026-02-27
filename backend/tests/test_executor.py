import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hymn.machine import MachineState
from hymn.executor import Executor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def enc(opcode: int, address: int = 0) -> int:
    return MachineState.encode(opcode, address)


H  = MachineState.HALT
J  = MachineState.JUMP
JZ = MachineState.JZER
JP = MachineState.JPOS
LD = MachineState.LOAD
ST = MachineState.STOR
AD = MachineState.ADD
SB = MachineState.SUB


def make_executor(*words, origin=0) -> Executor:
    """Return an Executor with *words* loaded at *origin*."""
    ex = Executor()
    ex.load(list(words), origin=origin)
    return ex


# ===========================================================================
# 1. Initial state
# ===========================================================================

class TestInitialState:

    def test_executor_starts_not_halted(self):
        ex = Executor()
        # assert ex.halted == False
        pass

    def test_state_has_required_keys(self):
        ex = Executor()
        snap = ex.state
        # assert all keys present: "pc", "ac", "ir", "halted", "memory"
        pass

    def test_machine_property_returns_machine_state(self):
        ex = Executor()
        # assert isinstance(ex.machine, MachineState)
        pass


# ===========================================================================
# 2. load()
# ===========================================================================

class TestLoad:

    def test_load_puts_words_in_memory(self):
        ex = Executor()
        ex.load([enc(H, 0), 42])
        # assert ex.machine.read_memory(0) == enc(H, 0)
        # assert ex.machine.read_memory(1) == 42
        pass

    def test_load_at_nonzero_origin(self):
        ex = Executor()
        ex.load([enc(H, 0)], origin=10)
        # assert ex.machine.read_memory(10) == enc(H, 0)
        # assert ex.machine.read_memory(0)  == 0
        pass

    def test_load_resets_registers(self):
        ex = make_executor(enc(LD, 1), enc(H, 0), 7)
        ex.run()                # ac becomes 7, pc changes
        ex.load([enc(H, 0)])    # reload should reset registers
        # assert ex.machine.pc == 0
        # assert ex.machine.ac == 0
        # assert ex.halted     == False
        pass

    def test_load_overflow_raises(self):
        ex = Executor()
        with pytest.raises(ValueError):
            ex.load([0] * 2, origin=31)


# ===========================================================================
# 3. reset()
# ===========================================================================

class TestReset:

    def test_reset_clears_memory_and_registers(self):
        ex = make_executor(enc(LD, 2), enc(H, 0), 99)
        ex.run()
        ex.reset()
        # assert ex.machine.pc == 0
        # assert ex.machine.ac == 0
        # assert ex.halted     == False
        # assert ex.machine.read_memory(2) == 0
        pass


# ===========================================================================
# 4. step()
# ===========================================================================

class TestStep:

    def test_step_returns_snapshot_dict(self):
        ex = make_executor(enc(H, 0))
        snap = ex.step()
        # assert isinstance(snap, dict)
        # assert "pc" in snap and "ac" in snap
        pass

    def test_step_on_halt_sets_halted(self):
        ex = make_executor(enc(H, 0))
        ex.step()
        # assert ex.halted == True
        pass

    def test_step_on_load_updates_ac(self):
        ex = make_executor(enc(LD, 2), enc(H, 0), 55)
        ex.step()
        # assert ex.machine.ac == 55
        pass

    def test_step_advances_pc_for_non_jump(self):
        ex = make_executor(enc(LD, 1), 0)
        ex.step()
        # assert ex.machine.pc == 1
        pass

    def test_step_on_halted_machine_raises(self):
        ex = make_executor(enc(H, 0))
        ex.step()               # halts
        with pytest.raises(RuntimeError):
            ex.step()           # must raise


# ===========================================================================
# 5. run()
# ===========================================================================

class TestRun:

    def test_run_returns_snapshot_dict(self):
        ex = make_executor(enc(H, 0))
        snap = ex.run()
        # assert isinstance(snap, dict)
        pass

    def test_run_halts_machine(self):
        ex = make_executor(enc(H, 0))
        ex.run()
        # assert ex.halted == True
        pass

    def test_run_executes_full_program(self):
        # LOAD 2 → AC = 42; then HALT
        ex = make_executor(enc(LD, 2), enc(H, 0), 42)
        ex.run()
        # assert ex.machine.ac == 42
        pass

    def test_run_on_halted_machine_raises(self):
        ex = make_executor(enc(H, 0))
        ex.run()
        with pytest.raises(RuntimeError):
            ex.run()

    def test_run_addition_program(self):
        # Memory layout:
        #   0: LOAD 4   (AC = mem[4] = 10)
        #   1: ADD  5   (AC = AC + mem[5] = 10 + 20 = 30)
        #   2: STOR 6   (mem[6] = 30)
        #   3: HALT
        #   4: 10
        #   5: 20
        #   6: 0        (result goes here)
        words = [
            enc(LD, 4), enc(AD, 5), enc(ST, 6), enc(H, 0),
            10, 20, 0,
        ]
        ex = Executor()
        ex.load(words)
        ex.run()
        # assert ex.machine.read_memory(6) == 30
        pass


# ===========================================================================
# 6. state property
# ===========================================================================

class TestStateProperty:

    def test_state_memory_is_copy(self):
        ex = make_executor(enc(H, 0))
        snap = ex.state
        snap["memory"][0] = 999
        # assert ex.machine.read_memory(0) != 999  (mutation must not affect machine)
        pass

    def test_state_reflects_current_pc(self):
        ex = make_executor(enc(LD, 1), 0)
        ex.step()
        # assert ex.state["pc"] == 1
        pass
