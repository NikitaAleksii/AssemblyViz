from enum import Enum
from dataclasses import dataclass


class OperandType(Enum):
    """The kinds of operand an instruction can accept."""
    ADDRESS = "address"   # 5-bit memory address (0–31)

    # Add new operand types here if the ISA ever grows


@dataclass(frozen=True)
class InstructionDef:
    """Static definition of one HYMN instruction.

    Attributes:
        mnemonic:  Assembly name (e.g. "ADD").
        opcode:    3-bit numeric opcode (0–7), matches MachineState constants.
        operands:  Tuple of OperandType describing each operand, in order.
                   Empty tuple means the instruction takes no operands.
    """
    mnemonic: str
    opcode: int
    operands: tuple[OperandType, ...]

    @property
    def operand_count(self) -> int:
        """Number of operands this instruction requires."""
        return len(self.operands)


# ---------------------------------------------------------------------------
# Registry  —  populated by _def() below; keyed by mnemonic (upper-case).

# Companion index keyed by opcode for executor lookups.
# ---------------------------------------------------------------------------
INSTRUCTIONS: dict[str, InstructionDef] = {}
INSTRUCTIONS_BY_OPCODE: dict[int, InstructionDef] = {}


def _def(mnemonic: str, opcode: int, *operands: OperandType) -> InstructionDef:
    """Create an InstructionDef and register it in INSTRUCTIONS and INSTRUCTIONS_BY_OPCODE."""
    defn = InstructionDef(mnemonic, opcode, operands)
    INSTRUCTIONS[mnemonic] = defn
    INSTRUCTIONS_BY_OPCODE[opcode] = defn
    return defn


# ---------------------------------------------------------------------------
# Instruction definitions  —  opcodes mirror MachineState constants.
# ---------------------------------------------------------------------------
    ''' 
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

    '''
# Example: ADD — AC = AC + memory[address]
ADD  = _def("ADD",  0b110, OperandType.ADDRESS)

HALT = _def("HALT", 0b000)

JUMP = _def("JUMP", 0b001, OperandType.ADDRESS)

JZER = _def("JZER", 0b010, OperandType.ADDRESS)

JPOS = _def("JPOS", 0b011, OperandType.ADDRESS)

LOAD = _def("LOAD", 0b100, OperandType.ADDRESS)

STOR = _def("STOR", 0b101, OperandType.ADDRESS)

SUB = _def("SUB", 0b111, OperandType.ADDRESS)





