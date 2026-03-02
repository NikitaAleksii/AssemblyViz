from __future__ import annotations
from hymn.executor import Executor
from hymn.machine import MachineState


class Debugger:
    """Adds breakpoint and step-through control on top of an Executor.

    A breakpoint is just a memory address.  When execution reaches an
    address that is in the breakpoint set, ``run_until_break()`` stops
    *before* executing the instruction at that address and returns the
    current state.

    Typical usage::

        ex = Executor()
        ex.load(words)
        dbg = Debugger(ex)
        dbg.add_breakpoint(5)
        state = dbg.run_until_break()   # stops when PC == 5
        state = dbg.step()              # execute the instruction at 5
    """

    def __init__(self, executor: Executor) -> None:
        """Attach the debugger to an already-loaded Executor.

        Args:
            executor: The Executor instance to control.
        """
        self._executor = executor
        self._breakpoints: set[int] = set()

    # ------------------------------------------------------------------
    # Breakpoint management
    # ------------------------------------------------------------------

    def add_breakpoint(self, address: int) -> None:
        """Register *address* as a breakpoint.

        Args:
            address: Memory address (0-31) at which to pause.

        Raises:
            ValueError: if *address* is outside 0-31.
        """
        if not (0 <= address < MachineState.MEMORY_SIZE):
            raise ValueError(
                f"Breakpoint address {address} out of range "
                f"(0-{MachineState.MEMORY_SIZE - 1})"
            )
        self._breakpoints.add(address)

    def remove_breakpoint(self, address: int) -> None:
        """Deregister *address*.  No-op if it was not set.

        Args:
            address: Memory address to remove.
        """
        self._breakpoints.discard(address)

    def clear_breakpoints(self) -> None:
        """Remove all breakpoints."""
        self._breakpoints.clear()

    @property
    def breakpoints(self) -> set[int]:
        """The current set of active breakpoint addresses (read-only copy)."""
        return set(self._breakpoints)

    # ------------------------------------------------------------------
    # Execution control
    # ------------------------------------------------------------------

    def step(self) -> dict:
        """Execute exactly one instruction and return the resulting state.

        Returns:
            Snapshot dict after the step.

        Raises:
            RuntimeError: if the machine is already halted.
        """
        return self._executor.step()

    def run_until_break(self) -> dict:
        """Run instructions until a breakpoint address is reached or the
        machine halts.

        Execution stops *before* the instruction at the breakpoint address
        is executed, so the returned PC will equal the breakpoint address.
        If no breakpoints are set this behaves like Executor.run().

        Returns:
            Snapshot dict at the moment execution paused.

        Raises:
            RuntimeError: if the machine is already halted before this call.
        """
        if self._executor.halted:
            raise RuntimeError("Machine is halted; call reset() to restart.")
        while not self._executor.halted:
            if self._executor.machine.pc in self._breakpoints:
                break
            self._executor.step()
        return self._executor.state

    # ------------------------------------------------------------------
    # State inspection (convenience pass-throughs)
    # ------------------------------------------------------------------

    @property
    def halted(self) -> bool:
        """True once the underlying machine has halted."""
        return self._executor.halted

    @property
    def state(self) -> dict:
        """Current machine state snapshot."""
        return self._executor.state
