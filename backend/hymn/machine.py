class MachineState:

    """
    Simulates the HYMN CPU: 3 registers (IR, PC, AC),
    32-byte memory, and 8 instructions with 3-bit opcodes.

    Every instruction is 8 bits packed like this:

    [opcode (3 bits) | address (5 bits)]
    bits 7-5           bits 4-0

    - 3 bits → 8 possible opcodes (0–7)
    - 5 bits → 32 possible addresses (0–31, matching memory size)

    
    registers:
    ┌───────────────────────────┬──────────────────────────────────────────────────────────┐
    │         Register          │                           Role                           │
    ├───────────────────────────┼──────────────────────────────────────────────────────────┤
    │ PC (Program Counter)      │ Points to the next instruction in memory to execute      │
    ├───────────────────────────┼──────────────────────────────────────────────────────────┤
    │ AC (Accumulator)          │ The one general-purpose register — all math happens here │
    ├───────────────────────────┼──────────────────────────────────────────────────────────┤
    | IR (Instruction Register) │ Holds the raw instruction word just fetched from memory  │
    └───────────────────────────┴──────────────────────────────────────────────────────────┘
    """

    MEMORY_SIZE = 32  # bytes

    # Memory-mapped I/O addresses (not shown as normal memory in the simulator)
    READ_ADDR  = 0b11110  # 30 — keyboard input  (used by LOAD 30 / READ pseudo-op)
    WRITE_ADDR = 0b11111  # 31 — console output  (used by STOR 31 / WRITE pseudo-op)

    # Opcode constants
    HALT = 0b000
    #Stop the machine 
    JUMP = 0b001
    #Set PC to address (unconditional jump)
    JZER = 0b010
    #Jump to address only if AC == 0  
    JPOS = 0b011
    #Jump to address only if AC >=0 
    LOAD = 0b100
    #AC = memory[address]  
    STOR = 0b101
    # memory[address] = AC  
    ADD  = 0b110
    # AC = AC + memory[address] 
    SUB  = 0b111
    #AC = AC - memory[address]  

    def __init__(self, input_fn=None, output_fn=None) -> None:
        """Initialise the machine with all registers zero and memory cleared.

        Args:
            input_fn:  Callable() -> int used for LOAD 30 (READ).
                       Defaults to prompting the console with ``input("? ")``.
            output_fn: Callable(int) used for STOR 31 (WRITE).
                       Defaults to ``print``.
        """
        self._input_fn  = input_fn  or (lambda: int(input("? ")))
        self._output_fn = output_fn or print
        self._io_output: list[int] = []
        self.reset()

    def reset(self) -> None:
        """Return every register and every memory cell to zero.
        Also clears the I/O output log."""
        self._memory = [0] * self.MEMORY_SIZE  # list of ints, each 0-255
        self._pc = 0   # program counter  (0-31)
        self._ac = 0   # accumulator      (signed Python int)
        self._ir = 0   # instruction register (raw 8-bit instruction word)
        self._halted = False
        self._io_output = []


    def read_memory(self, address: int) -> int:
        """Return the value stored at *address* (0-31)."""
        self._check_address(address)
        return self._memory[address]

    def write_memory(self, address: int, value: int) -> None:
        """Write *value* to *address* (0-31).

        Values are stored as-is; callers are responsible for keeping them
        in a meaningful range (0-255 for instruction words, any int for data).
        """
        self._check_address(address)
        self._memory[address] = value

    def load_program(self, words: list[int], origin: int = 0) -> None:
        """Load a list of instruction/data words into memory starting at *origin*."""
        if origin + len(words) > self.MEMORY_SIZE:
            raise ValueError(
                f"Program of {len(words)} words at origin {origin} "
                f"exceeds memory size {self.MEMORY_SIZE}"
            )
        for offset, word in enumerate(words):
            self._memory[origin + offset] = word

    def _check_address(self, address: int) -> None:
        if not (0 <= address < self.MEMORY_SIZE):
            raise ValueError(
                f"Memory address {address} out of range (0-{self.MEMORY_SIZE - 1})"
            )


    @property
    def pc(self) -> int:
        """Program counter (0-31)."""
        return self._pc

    @pc.setter
    def pc(self, value: int) -> None:
        if not (0 <= value < self.MEMORY_SIZE):
            raise ValueError(f"PC value {value} out of range (0-{self.MEMORY_SIZE - 1})")
        self._pc = value

    @property
    def ac(self) -> int:
        """Accumulator — the sole general-purpose register."""
        return self._ac

    @ac.setter
    def ac(self, value: int) -> None:
        self._ac = value

    @property
    def ir(self) -> int:
        """Instruction register — raw 8-bit word fetched from memory."""
        return self._ir


    @staticmethod
    def decode(instruction: int) -> tuple[int, int]:
        """Split an 8-bit instruction word into (opcode, address).

        Returns:
            opcode  : int in 0-7  (high 3 bits)
            address : int in 0-31 (low 5 bits)
        """
        opcode  = (instruction >> 5) & 0b111
        address = instruction & 0b11111
        return opcode, address

    @staticmethod
    def encode(opcode: int, address: int) -> int:
        """Combine a 3-bit opcode and 5-bit address into one 8-bit word."""
        if not (0 <= opcode <= 7):
            raise ValueError(f"Opcode {opcode} out of range (0-7)")
        if not (0 <= address < 32):
            raise ValueError(f"Address {address} out of range (0-31)")
        return (opcode << 5) | address


    def step(self) -> None:
        """Fetch and execute one instruction, updating PC, AC, and IR.

        Raises RuntimeError if the machine is already halted.
        ┌────────┬─────────────────────────────────────┬─────────────────────────────┐
        │ Opcode │         What happens to PC          │ What happens to AC / memory │
        ├────────┼─────────────────────────────────────┼─────────────────────────────┤
        │ HALT   │ unchanged                           │ _halted = True              │
        ├────────┼─────────────────────────────────────┼─────────────────────────────┤
        │ JUMP   │ PC = address                        │ nothing                     │
        ├────────┼─────────────────────────────────────┼─────────────────────────────┤
        │ JZER   │ PC = address if AC==0, else PC += 1 │ nothing                     │
        ├────────┼─────────────────────────────────────┼─────────────────────────────┤
        │ JPOS   │ PC = address if AC>0, else PC += 1  │ nothing                     │
        ├────────┼─────────────────────────────────────┼─────────────────────────────┤
        │ LOAD   │ PC += 1                             │ AC = memory[address]        │
        ├────────┼─────────────────────────────────────┼─────────────────────────────┤
        │ STOR   │ PC += 1                             │ memory[address] = AC        │
        ├────────┼─────────────────────────────────────┼─────────────────────────────┤
        │ ADD    │ PC += 1                             │ AC = AC + memory[address]   │
        ├────────┼─────────────────────────────────────┼─────────────────────────────┤
        │ SUB    │ PC += 1                             │ AC = AC - memory[address]   │
        └────────┴─────────────────────────────────────┴─────────────────────────────┘
        """
        if self._halted:
            raise RuntimeError("Machine is halted; call reset() to restart.")

        # Fetch
        self._ir = self._memory[self._pc]

        # Decode
        opcode, address = self.decode(self._ir)

        # Execute
        if opcode == self.HALT:
            self._halted = True
            # pc unchanged, _halted = True

        elif opcode == self.JUMP:
            self._pc = address
            # PC = address, nothing happens to AC/memory

        elif opcode == self.JZER:
            if self._ac == 0:
                self._pc = address
            else:
                self._pc += 1
            # PC = address if AC==0, else PC += 1, nothing happens to AC/memory

        elif opcode == self.JPOS:
            if self._ac > 0:
                self._pc = address
            else:
                self._pc += 1
                #PC = address if AC>0, else PC += 1, nothing happens to AC/memory

        elif opcode == self.LOAD:
            if address == self.READ_ADDR:
                self._ac = self._input_fn()   # memory-mapped keyboard input
            else:
                self._ac = self._memory[address]
            self._pc += 1
            #PC += 1, AC = memory[address] (or keyboard if address == READ_ADDR)

        elif opcode == self.STOR:
            if address == self.WRITE_ADDR:
                self._output_fn(self._ac)     # memory-mapped console output
                self._io_output.append(self._ac)
            else:
                self._memory[address] = self._ac
            self._pc += 1
            #PC += 1, memory[address] = AC (or console if address == WRITE_ADDR)

        elif opcode == self.ADD:
            self._ac = self._ac + self._memory[address]
            self._pc += 1
            #PC += 1, AC = AC + memory[address] 

        elif opcode == self.SUB:
            self._ac = self._ac - self._memory[address]
            self._pc += 1
            #PC += 1, AC = AC - memory[address] 



    def run(self) -> None:
        """Execute instructions until HALT or PC goes out of bounds."""
        if self._halted:
            raise RuntimeError("Machine is halted; call reset() to restart.")
        while not self._halted:
            self.step()


    @property
    def halted(self) -> bool:
        """True once a HALT instruction has been executed."""
        return self._halted


    def snapshot(self) -> dict:
        """Return a JSON-serialisable dict of the complete machine state."""
        return {
            "pc":        self._pc,
            "ac":        self._ac,
            "ir":        self._ir,
            "zero_flag": 'true' if self._ac == 0 else 'false',
            "positive_flag": 'true' if self._ac > 0 else 'false',
            "halted":    self._halted,
            "memory":    list(self._memory),
            "io_output": list(self._io_output),
        }

    def __repr__(self) -> str:
        opcode, address = self.decode(self._ir)
        mnemonic = [
            "HALT", "JUMP", "JZER", "JPOS",
            "LOAD", "STOR", "ADD",  "SUB",
        ][opcode]
        halted = " HALTED" if self._halted else ""
        return (
            f"<HYMN pc={self._pc:02d} ac={self._ac} "
            f"ir={mnemonic}({address}){halted}>"
        )
