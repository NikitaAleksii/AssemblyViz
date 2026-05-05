from __future__ import annotations
from hymn.machine import MachineState


class Executor:
    """High-level runner for HYMN programs.

    Wrapper for MachineState and exposes a simple step / run API.

    author: RV
    """

    def __init__(self, input_fn=None, output_fn=None) -> None:
        """Create an Executor backed by a freshly reset MachineState.

        parameters:
            input_fn:  Passed to MachineState for READ (LOAD 30) handling.
            output_fn: Passed to MachineState for WRITE (STOR 31) handling.
        """
        self._machine = MachineState(input_fn=input_fn, output_fn=output_fn)

    # Program management

    def load(self, words: list[int], origin: int = 0) -> None:
        """Load machine words into memory starting at *origin*, then reset
        the registers (PC, AC, IR) so execution begins from *origin*.

        parameters:
            words:  List of 8-bit instruction/data words.
            origin: Starting memory address (0-31, default 0).
        """
        self._machine.reset()
        self._machine.load_program(words, origin)

    def reset(self) -> None:
        """Reset all registers and clear memory back to zero."""
        self._machine.reset()

    # Execution

    def step(self) -> dict:
        """Fetch and execute one instruction.

        Returns:
            A snapshot dict (see MachineState.snapshot) reflecting the
            machine state *after* the instruction has executed.

        
        raises RuntimeError: if the machine is already halted.
        """
        self._machine.step()
        return self._machine.snapshot()

    def run(self) -> dict:
        """Execute instructions until a HALT is reached.

        Returns:
            A snapshot dict reflecting the final halted state.

        raises RuntimeError if the machine is already halted before run() is called.
        """
        self._machine.run()
        return self._machine.snapshot()

    # State inspection

    @property
    def halted(self) -> bool:
        """True once a HALT instruction has executed."""
        return self._machine.halted

    @property
    def state(self) -> dict:
        """Current machine state as a JSON-serialisable dict.

        Keys: ``"pc"``, ``"ac"``, ``"ir"``, ``"halted"``, ``"memory"``.
        """
        return self._machine.snapshot()

    @property
    def machine(self) -> MachineState:
        """Direct access to the underlying MachineState (for advanced use)."""
        return self._machine
