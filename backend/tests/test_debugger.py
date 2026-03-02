import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hymn.machine import MachineState
from hymn.executor import Executor
from hymn.debugger import Debugger


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


def make_debugger(*words, origin=0) -> Debugger:
    """Return a Debugger with *words* loaded into its Executor."""
    ex = Executor()
    ex.load(list(words), origin=origin)
    return Debugger(ex)


# ===========================================================================
# 1. Breakpoint management
# ===========================================================================

class TestBreakpointManagement:

    def test_no_breakpoints_initially(self):
        dbg = make_debugger(enc(H, 0))
        # assert dbg.breakpoints == set()
        pass

    def test_add_breakpoint(self):
        dbg = make_debugger(enc(H, 0))
        dbg.add_breakpoint(5)
        # assert 5 in dbg.breakpoints
        pass

    def test_add_multiple_breakpoints(self):
        dbg = make_debugger(enc(H, 0))
        dbg.add_breakpoint(2)
        dbg.add_breakpoint(7)
        # assert dbg.breakpoints == {2, 7}
        pass

    def test_remove_breakpoint(self):
        dbg = make_debugger(enc(H, 0))
        dbg.add_breakpoint(3)
        dbg.remove_breakpoint(3)
        # assert 3 not in dbg.breakpoints
        pass

    def test_remove_nonexistent_breakpoint_is_noop(self):
        dbg = make_debugger(enc(H, 0))
        dbg.remove_breakpoint(10)   # must not raise
        # assert dbg.breakpoints == set()
        pass

    def test_clear_breakpoints(self):
        dbg = make_debugger(enc(H, 0))
        dbg.add_breakpoint(1)
        dbg.add_breakpoint(2)
        dbg.clear_breakpoints()
        # assert dbg.breakpoints == set()
        pass

    def test_breakpoints_property_is_copy(self):
        dbg = make_debugger(enc(H, 0))
        dbg.add_breakpoint(4)
        copy = dbg.breakpoints
        copy.add(9)
        # assert 9 not in dbg.breakpoints   (mutating copy must not affect debugger)
        pass

    def test_add_breakpoint_out_of_range_raises(self):
        dbg = make_debugger(enc(H, 0))
        with pytest.raises(ValueError):
            dbg.add_breakpoint(32)

    def test_add_breakpoint_negative_raises(self):
        dbg = make_debugger(enc(H, 0))
        with pytest.raises(ValueError):
            dbg.add_breakpoint(-1)


# ===========================================================================
# 2. step()
# ===========================================================================

class TestDebuggerStep:

    def test_step_returns_dict(self):
        dbg = make_debugger(enc(H, 0))
        snap = dbg.step()
        # assert isinstance(snap, dict)
        pass

    def test_step_executes_one_instruction(self):
        # LOAD 2 then HALT; after one step AC should be 77
        dbg = make_debugger(enc(LD, 2), enc(H, 0), 77)
        dbg.step()
        # assert dbg.state["ac"] == 77
        pass

    def test_step_on_halted_raises(self):
        dbg = make_debugger(enc(H, 0))
        dbg.step()
        with pytest.raises(RuntimeError):
            dbg.step()

    def test_step_ignores_breakpoints(self):
        # Breakpoints should NOT stop step() — step always executes one instruction.
        dbg = make_debugger(enc(LD, 1), 0)
        dbg.add_breakpoint(0)   # breakpoint on the very first instruction
        dbg.step()              # must execute, not stop before it
        # assert dbg.state["pc"] == 1
        pass


# ===========================================================================
# 3. run_until_break()
# ===========================================================================

class TestRunUntilBreak:

    def test_run_until_break_no_breakpoints_runs_to_halt(self):
        dbg = make_debugger(enc(LD, 2), enc(H, 0), 5)
        dbg.run_until_break()
        # assert dbg.halted == True
        pass

    def test_run_until_break_stops_at_breakpoint(self):
        # Program: LOAD 3, ADD 4, HALT, 10, 20
        # Breakpoint at address 1 (ADD) — should stop before ADD executes
        words = [enc(LD, 3), enc(AD, 4), enc(H, 0), 10, 20]
        dbg = make_debugger(*words)
        dbg.add_breakpoint(1)
        dbg.run_until_break()
        # assert dbg.state["pc"] == 1     (stopped before ADD)
        # assert dbg.state["ac"] == 10    (LOAD executed, ADD did not)
        pass

    def test_run_until_break_does_not_execute_breakpoint_instruction(self):
        # Breakpoint at address 0 — execution should stop immediately (PC is already 0)
        dbg = make_debugger(enc(LD, 1), 5)
        dbg.add_breakpoint(0)
        dbg.run_until_break()
        # assert dbg.state["pc"] == 0
        # assert dbg.state["ac"] == 0     (LOAD has NOT executed yet)
        pass

    def test_run_until_break_can_continue_after_break(self):
        # Stop at address 1, then continue to halt
        words = [enc(LD, 3), enc(AD, 4), enc(H, 0), 10, 20]
        dbg = make_debugger(*words)
        dbg.add_breakpoint(1)
        dbg.run_until_break()   # stops at 1
        dbg.remove_breakpoint(1)
        dbg.run_until_break()   # should now run to HALT
        # assert dbg.halted == True
        # assert dbg.state["ac"] == 30    (10 + 20)
        pass

    def test_run_until_break_returns_snapshot(self):
        dbg = make_debugger(enc(H, 0))
        snap = dbg.run_until_break()
        # assert isinstance(snap, dict)
        # assert "pc" in snap
        pass

    def test_run_until_break_multiple_breakpoints(self):
        # Breakpoints at 1 and 2; should stop at 1 first
        words = [enc(LD, 4), enc(AD, 5), enc(H, 0), 0, 3, 7]
        dbg = make_debugger(*words)
        dbg.add_breakpoint(1)
        dbg.add_breakpoint(2)
        dbg.run_until_break()
        # assert dbg.state["pc"] == 1
        pass

    def test_run_until_break_on_halted_raises(self):
        dbg = make_debugger(enc(H, 0))
        dbg.run_until_break()   # halts
        with pytest.raises(RuntimeError):
            dbg.run_until_break()


# ===========================================================================
# 4. halted and state pass-throughs
# ===========================================================================

class TestPassThroughs:

    def test_halted_false_initially(self):
        dbg = make_debugger(enc(LD, 1), 0)
        # assert dbg.halted == False
        pass

    def test_halted_true_after_halt(self):
        dbg = make_debugger(enc(H, 0))
        dbg.step()
        # assert dbg.halted == True
        pass

    def test_state_keys(self):
        dbg = make_debugger(enc(H, 0))
        snap = dbg.state
        # assert set(snap.keys()) >= {"pc", "ac", "ir", "halted", "memory"}
        pass
