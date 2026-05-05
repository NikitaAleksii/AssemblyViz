# HYMN — UML Class Diagram

```mermaid
classDiagram
    class OperandType {
        <<enumeration>>
        ADDRESS
    }

    class InstructionDef {
        <<dataclass>>
        +mnemonic : str
        +opcode : int
        +operands : tuple
        +operand_count() int
    }

    class ParseError {
        <<dataclass>>
        +line_number : int
        +line_text : str
        +message : str
    }

    class Parser {
        -_errors : list
        -_symbol_table : dict
        +parse(source : str) list
        +errors() list
        +symbol_table() dict
    }

    class MachineState {
        +MEMORY_SIZE : int
        +READ_ADDR : int
        +WRITE_ADDR : int
        -_memory : list
        -_pc : int
        -_ac : int
        -_ir : int
        -_halted : bool
        -_io_output : list
        +reset()
        +read_memory(address : int) int
        +write_memory(address : int, value : int)
        +load_program(words : list, origin : int)
        +decode(instruction : int) tuple
        +encode(opcode : int, address : int) int
        +step()
        +run()
        +snapshot() dict
        +pc() int
        +ac() int
        +ir() int
        +halted() bool
    }

    class Executor {
        -_machine : MachineState
        +load(words : list, origin : int)
        +reset()
        +step() dict
        +run() dict
        +halted() bool
        +state() dict
        +machine() MachineState
    }

    class Debugger {
        -_executor : Executor
        -_breakpoints : set
        +add_breakpoint(address : int)
        +remove_breakpoint(address : int)
        +clear_breakpoints()
        +breakpoints() set
        +step() dict
        +run_until_break() dict
        +halted() bool
        +state() dict
    }

    Debugger *-- Executor : contains
    Executor *-- MachineState : contains
    Parser ..> ParseError : creates
    Parser ..> InstructionDef : uses
    InstructionDef --> OperandType : has operands
```

## Notes

| Symbol | Meaning |
|--------|---------|
| `*--`  | Composition (owner controls lifetime) |
| `-->`  | Association |
| `..>`  | Dependency (uses transiently) |
| `+`    | Public |
| `-`    | Private |

**Instruction word format (8-bit):** `[opcode (3 bits) | address (5 bits)]`

**Data flow:** Source code → `Parser.parse()` → `list[int]` → `Executor.load()` → `MachineState` → `Executor.step()/run()` → snapshot `dict`
