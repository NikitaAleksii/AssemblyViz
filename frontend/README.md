# AssemblyViz — Frontend

Interactive assembly simulator UI built with React + TypeScript + Vite. Supports two ISA modes: **HYMN** (a simple educational ISA) and **RISC-V**.

## Features

- **Code editor** with line numbers and syntax-aware placeholder
- **Step-by-step execution** — forward and backward through instructions
- **Play / pause** with configurable speed (via slider)
- **Resizable panels** — draggable divider between the code editor and output section
- **Memory panel** — live view of memory slots with change-flash animation; switchable between Hexadecimal, Decimal, and Instruction display formats
- **Results panel** — assembled instruction listing (address, machine code, mnemonic) with active-row highlighting; exportable as `.txt`
- **Register panel** — real-time register values (3 registers for HYMN, 32 for RISC-V); switchable display format
- **Input queue** — (HYMN only) supply integers consumed by the `READ` pseudo-op, one per line
- **ISA toggle** — switching modes resets all simulation state instantly
- **Import / Export** — load source from a `.txt` file or save source/assembled results to disk

## Getting Started

```bash
# Install dependencies
npm install

# Start dev server (proxies /api/* to the backend)
npm run dev

# Type-check and build for production
npm run build

# Preview production build locally
npm run preview
```

The dev server runs on `http://localhost:5173` by default. API calls (`/api/hymn/*`, `/api/riscv/*`) are proxied to the backend running on `http://localhost:8000`.

## Project Structure

```
src/
  assets/
    backwards.svg     # Step-back button icon
    forward.svg       # Step-forward button icon
    logo.svg          # App logo
    play.svg          # Play button icon
    reset.svg         # Reset button icon
  components/
    CodeEditor.tsx      # Left panel: editor, input queue, assemble button, output bar
    ErrorBoundary.tsx   # React error boundary wrapping the app shell
    MemoryPanel.tsx     # Left panel (Memory tab): memory slot table
    Navbar.tsx          # Top bar: tabs, playback controls, speed slider, ISA toggle
    RegisterPanel.tsx   # Right panel: register table
    ResultsPanel.tsx    # Center panel: assembled instruction listing
  types/
    index.ts            # Shared types, ISA constants, and memory/register builders
  App.css               # All component styles
  App.tsx               # Root component — owns all simulation state and API calls
  index.css
  main.tsx              # React entry point
index.html
```

## ISA Modes

### HYMN
- 3 registers: `PC`, `IR`, `AC`
- 32 memory slots with 5-bit binary addresses
- Stateful stepping: the backend advances machine state one instruction per call
- Input queue feeds integers to the `READ` pseudo-op

### RISC-V
- 32 registers (`x0`–`x31` with ABI names)
- Memory panel mirrors the instruction list; one slot per instruction
- Stateless replay: the backend re-simulates from scratch up to N steps per call, so step-back is fully supported

## Backend API

The frontend expects a backend at the same origin exposing:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/hymn/assemble` | POST | Assemble HYMN source, return instructions + memory + registers |
| `/api/hymn/step` | POST | Execute one HYMN instruction given current machine state |
| `/api/riscv/assemble` | POST | Assemble RISC-V source, return instructions + registers |
| `/api/riscv/step` | POST | Replay RISC-V source to `step_count` instructions |
