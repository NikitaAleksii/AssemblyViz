from __future__ import annotations
from hymn.machine import MachineState


class Executor:
    """High-level runner for HYMN programs.

    Wraps a MachineState and exposes a simple step / run API.
    Callers load a program once, then drive execution step-by-step
    or all-at-once, and inspect the machine state after each action.

    Typical usage::

        ex = Executor()
        ex.load([0b10000010, 0b00000000])   # LOAD 2, HALT
        ex.run()
        print(ex.state)
    """

    def __init__(self) -> None:
        """Create an Executor backed by a freshly reset MachineState."""
        pass

    # ------------------------------------------------------------------
    # Program management
    # ------------------------------------------------------------------

    def load(self, words: list[int], origin: int = 0) -> None:
        """Load machine words into memory starting at *origin*, then reset
        the registers (PC, AC, IR) so execution begins from *origin*.

        Args:
            words:  List of 8-bit instruction/data words.
            origin: Starting memory address (0-31, default 0).
        """
        pass

    def reset(self) -> None:
        """Reset all registers and clear memory back to zero."""
        pass

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def step(self) -> dict:
        """Fetch and execute one instruction.

        Returns:
            A snapshot dict (see MachineState.snapshot) reflecting the
            machine state *after* the instruction has executed.

        Raises:
            RuntimeError: if the machine is already halted.
        """
        pass

    def run(self) -> dict:
        """Execute instructions until a HALT is reached.

        Returns:
            A snapshot dict reflecting the final halted state.

        Raises:
            RuntimeError: if the machine is already halted before run() is called.
        """
        pass

    # ------------------------------------------------------------------
    # State inspection
    # ------------------------------------------------------------------

    @property
    def halted(self) -> bool:
        """True once a HALT instruction has executed."""
        pass

    @property
    def state(self) -> dict:
        """Current machine state as a JSON-serialisable dict.

        Keys: ``"pc"``, ``"ac"``, ``"ir"``, ``"halted"``, ``"memory"``.
        """
        pass

    @property
    def machine(self) -> MachineState:
        """Direct access to the underlying MachineState (for advanced use)."""
        pass
