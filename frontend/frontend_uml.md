# Frontend — UML Class Diagram

```mermaid
classDiagram
    %% ── Shared TypeScript Types ──────────────────────────────────────────

    class ISAMode {
        <<type>>
        HYMN
        RISC-V
    }

    class DisplayFormat {
        <<type>>
        HEXADECIMAL
        DECIMAL
        INSTRUCTION
    }

    class AssembledInstruction {
        <<interface>>
        +address : string
        +code : string
        +instruction : string
        +isActive : boolean
    }

    class MemorySlot {
        <<interface>>
        +address : string
        +instruction : string
        +value : number
        +isActive : boolean
        +isChanged : boolean
    }

    class Register {
        <<interface>>
        +name : string
        +number : number
        +value : number
    }

    class HistoryEntry {
        <<interface>>
        +registers : Register[]
        +memorySlots : MemorySlot[]
        +currentStep : number
        +inputQueuePos : number
    }

    %% ── Components ───────────────────────────────────────────────────────

    class App {
        <<component>>
        -leftWidth : number
        -code : string
        -output : string
        -isError : boolean
        -consoleOutput : string
        -isaMode : ISAMode
        -speedMs : number
        -activeTab : string
        -memoryFormat : DisplayFormat
        -registerFormat : DisplayFormat
        -words : number[]
        -assembled : AssembledInstruction[]
        -memorySlots : MemorySlot[]
        -registers : Register[]
        -currentStep : number
        -inputQueue : string[]
        -stepHistory : HistoryEntry[]
        +handleAssemble() Promise
        +performStep() Promise
        +handleStep() Promise
        +handleBack()
        +handlePlay() Promise
        +handleReset()
        +handleExport()
        +handleExportResults()
    }

    class Navbar {
        <<component>>
        +activeTab : string
        +isaMode : ISAMode
        +speedMs : number
        +onTabChange(tab)
        +onISAChange(mode)
        +onSpeedChange(ms)
        +onBack()
        +onPlay()
        +onStep()
        +onReset()
    }

    class CodeEditor {
        <<component>>
        +code : string
        +output : string
        +isError : boolean
        +consoleOutput : string
        +isaMode : string
        +inputQueue : string[]
        +onCodeChange(code)
        +onAssemble()
        +onExport()
        +onInputQueueChange(lines)
    }

    class MemoryPanel {
        <<component>>
        +slots : MemorySlot[]
        +displayFormat : DisplayFormat
        +onFormatChange(fmt)
    }

    class ResultsPanel {
        <<component>>
        +instructions : AssembledInstruction[]
        +onExportResults()
    }

    class RegisterPanel {
        <<component>>
        +registers : Register[]
        +displayFormat : DisplayFormat
        +onFormatChange(fmt)
    }

    %% ── Component Hierarchy ──────────────────────────────────────────────

    App *-- Navbar : renders
    App *-- CodeEditor : renders (editor tab)
    App *-- MemoryPanel : renders (memory tab)
    App *-- ResultsPanel : renders
    App *-- RegisterPanel : renders

    %% ── Type Usage ───────────────────────────────────────────────────────

    App --> ISAMode : uses
    App --> DisplayFormat : uses
    App --> AssembledInstruction : manages
    App --> MemorySlot : manages
    App --> Register : manages
    App --> HistoryEntry : manages
    Navbar --> ISAMode : receives
    MemoryPanel --> MemorySlot : displays
    MemoryPanel --> DisplayFormat : uses
    ResultsPanel --> AssembledInstruction : displays
    RegisterPanel --> Register : displays
    RegisterPanel --> DisplayFormat : uses
```

## Notes

| Symbol | Meaning |
|--------|---------|
| `*--`  | Composition (App renders and owns child) |
| `-->`  | Dependency (receives / uses type) |
| `+`    | Prop (public input) |
| `-`    | State (internal to App) |

**Architecture:** All state lives in `App` and flows down as props. Every child component is fully controlled — no local state. Communication back to `App` is via callback props (`onXxx`).

**API calls** (made by `App` only):
- `POST /api/{hymn|riscv}/assemble` — triggered by `handleAssemble()`
- `POST /api/hymn/step` — stateful; passes `{ memory, pc, ac, io_input }`
- `POST /api/riscv/step` — stateless replay; passes `{ source, step_count }`
