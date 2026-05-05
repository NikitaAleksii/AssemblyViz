# RISC-V — UML Class Diagram

```mermaid
classDiagram
    class Registers {
        -regs : list
        +read(index : int) int
        +write(index : int, value : int)
    }

    class Memory {
        +memory : list
        +depth : int
        +addr_width : int
        +memory_slots : int
        +memory_reset()
        +memory_write(address : int, value : int, mask : str)
        +memory_read(address : int) int
        +memory_print()
    }

    class InstructionOpcodes {
        <<constants>>
        +OPreg : int
        +OPimm : int
        +LOAD : int
        +STORE : int
        +BRANCH : int
        +JAL : int
        +JALR : int
        +LUI : int
        +AUIPC : int
        +SYSTEM : int
    }

    class ParsedLine {
        <<dataclass>>
        +line_number : int
        +label : str
        +mnemonic : str
        +operands : list
        +data_words : list
    }

    class ParseError {
        <<dataclass>>
        +line_number : int
        +line_text : str
        +message : str
    }

    class Parser {
        -_parsed_lines : list
        -_symbol_table : dict
        -_errors : list
        -_text_lines : list
        -_data_lines : list
        +parse(source : str) list
        +symbol_table() dict
        +errors() list
    }

    class Assembler {
        -_pc : int
        -_labels : dict
        +assemble(parsed_lines : list, symbol_table : dict) list
    }

    class DecodedInstruction {
        +opcode : int
        +rd : int
        +rs1 : int
        +rs2 : int
        +funct3 : int
        +funct7 : int
        +isOPreg : bool
        +isOPimm : bool
        +isLoad : bool
        +isStore : bool
        +isBranch : bool
        +isJal : bool
        +isJalr : bool
        +isLUI : bool
        +isAUIPC : bool
        +isSystem : bool
        +Iimm : int
        +Simm : int
        +Bimm : int
        +Jimm : int
        +Uimm : int
    }

    class Simulation {
        +memory_depth : int
        +PC : int
        +halted : bool
        -_symbol_table : dict
        -_errors : list
        -_io_output : list
        +load(source : str)
        +step() dict
        +reset()
        +read_label(label : str, count : int) list
        +snapshot() dict
    }

    Simulation *-- Memory : contains
    Simulation *-- Registers : contains
    Simulation ..> Parser : uses
    Simulation ..> Assembler : uses
    Simulation ..> DecodedInstruction : creates
    Parser ..> ParsedLine : produces
    Parser ..> ParseError : produces
    Assembler ..> ParsedLine : consumes
    Assembler ..> InstructionOpcodes : uses
    DecodedInstruction ..> InstructionOpcodes : uses
```

## Notes

| Symbol | Meaning |
|--------|---------|
| `*--`  | Composition (owner controls lifetime) |
| `..>`  | Dependency (uses transiently) |
| `+`    | Public |
| `-`    | Private |

**Instruction encoding formats:** R · I · S · B · U · J (all 32-bit words)

**Data flow:** Source code → `Parser.parse()` → `list[ParsedLine]` + symbol table → `Assembler.assemble()` → `list[int]` (32-bit words) → `Memory` → fetch/decode via `DecodedInstruction` → `Simulation._execute()`
