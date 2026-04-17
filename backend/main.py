# FastAPI backend server — bridges the frontend UI with the Python assembler/simulator engine

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from hymn.parser import Parser as HymnParser
from hymn.machine import MachineState
from riscv.parser import Parser as RiscvParser
from riscv.assembler import Assembler as RiscvAssembler
from riscv.simulation import Simulation
from riscv.isa import DIRECTIVES

# Creates the FastAPI app and allows the Vite dev server (port 5173) to make requests via CORS
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request models that define what JSON must send ────────────────────────────

class HymnAssembleRequest(BaseModel):
    source: str

class HymnStepRequest(BaseModel):
    memory: list[int]   # full 32-byte snapshot
    pc: int
    ac: int
    io_input: int = 0   # value supplied by READ pseudo-op

class RiscvAssembleRequest(BaseModel):
    source: str

class RiscvStepRequest(BaseModel):
    source: str
    step_count: int  # number of machine words to execute

# ── HYMN helpers ──────────────────────────────────────────────────────────────

_HYMN_MNEMONICS = ["HALT", "JUMP", "JZER", "JPOS", "LOAD", "STOR", "ADD", "SUB"]

def _decode_hymn_word(word: int) -> str:
    """Decode a raw 8-bit word into a human-readable mnemonic like "ADD 5" or "READ"."""
    opcode  = (word >> 5) & 0b111
    address = word & 0b11111
    if opcode == 0:
        return "HALT"
    if opcode == 0b100 and address == 30:   # LOAD 30 = READ pseudo-op
        return "READ"
    if opcode == 0b101 and address == 31:   # STOR 31 = WRITE pseudo-op
        return "WRITE"
    return f"{_HYMN_MNEMONICS[opcode]} {address}"

def _hymn_memory_slots(memory: list[int]) -> list[dict]:
    """Build a display array with address, raw value, and decoded instruction for each memory slot."""
    return [
        {
            "address": bin(i)[2:].zfill(5),
            "value":   memory[i],
            "decoded": _decode_hymn_word(memory[i]),
        }
        for i in range(len(memory))
    ]

def _hymn_instruction_lines(source: str) -> list[str]:
    """Strip comments and labels from source, returning bare instruction tokens for the results panel."""
    result = []
    for raw in source.splitlines():
        stripped = raw.split(';')[0].split('#')[0].strip().upper()
        if not stripped:
            continue
        tokens = stripped.split()
        if tokens[0].endswith(':'):
            tokens = tokens[1:]
        if not tokens:
            continue
        result.append(' '.join(tokens))
    return result

# ── RISC-V helpers ────────────────────────────────────────────────────────────

_DATA_DIRECTIVES = DIRECTIVES - {".text", ".data"}

def _riscv_build_display(parsed_lines, symbol_table) -> list[dict]:
    """Build one display row per emitted machine word.

    Pseudo-instructions that expand to multiple words have their continuation
    rows marked with a "↳" symbol.
    """
    assembler = RiscvAssembler()
    assembler._labels = symbol_table
    assembler._pc = 0
    rows = []
    for pl in parsed_lines:
        if pl.mnemonic in _DATA_DIRECTIVES:
            for dw in (pl.data_words or []):
                rows.append({
                    "address":     f"0x{assembler._pc:08x}",
                    "code":        f"0x{dw:08x}",
                    "instruction": pl.mnemonic,
                })
                assembler._pc += 4
        else:
            src_text = f"{pl.mnemonic} {' '.join(pl.operands)}"
            emitted = assembler._assemble_pseudo([pl.mnemonic] + pl.operands)
            for j, w in enumerate(emitted):
                rows.append({
                    "address":     f"0x{assembler._pc + j * 4:08x}",
                    "code":        f"0x{w:08x}",
                    "instruction": src_text if j == 0 else "↳",
                })
            assembler._pc += len(emitted) * 4
    return rows


# ── HYMN endpoints ────────────────────────────────────────────────────────────

@app.post("/api/hymn/assemble")
def hymn_assemble(req: HymnAssembleRequest):
    """Parse and assemble HYMN source, returning instructions, memory display, and initial registers."""
    parser = HymnParser()
    words = parser.parse(req.source)
    if words is None:
        errors = [{"line": e.line_number, "message": e.message} for e in parser.errors]
        raise HTTPException(status_code=400, detail={"errors": errors})

    instr_lines = _hymn_instruction_lines(req.source)
    assembled = [
        {
            "address":     bin(i)[2:].zfill(5),
            "code":        bin(w)[2:].zfill(8),
            "instruction": instr_lines[i] if i < len(instr_lines) else "",
        }
        for i, w in enumerate(words)
    ]

    machine = MachineState(input_fn=lambda: 0, output_fn=lambda v: None)
    machine.load_program(words)
    snap = machine.snapshot()

    return {
        "words":        words,
        "instructions": assembled,
        "memory":       _hymn_memory_slots(snap["memory"]),
        "registers":    {"pc": snap["pc"], "ac": snap["ac"], "ir": snap["ir"], "halted": snap["halted"]},
    }

@app.post("/api/hymn/step")
def hymn_step(req: HymnStepRequest):
    """Execute one HYMN instruction.

    Reconstructs machine state from the memory/PC/AC sent by the frontend
    (the backend is stateless), runs one step, and returns updated registers,
    memory, halt status, and any console output.
    """
    machine = MachineState(input_fn=lambda: req.io_input, output_fn=lambda v: None)
    if len(req.memory) != 32:
        raise HTTPException(status_code=400, detail="Memory must be exactly 32 bytes")
    try:
        for i, val in enumerate(req.memory):
            machine.write_memory(i, val)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    machine.pc = req.pc
    machine.ac = req.ac

    try:
        machine.step()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    snap = machine.snapshot()
    return {
        "pc":        snap["pc"],
        "ac":        snap["ac"],
        "ir":        snap["ir"],
        "halted":    snap["halted"],
        "memory":    _hymn_memory_slots(snap["memory"]),
        "io_output": snap["io_output"],
    }

# ── RISC-V endpoints ──────────────────────────────────────────────────────────

@app.post("/api/riscv/assemble")
def riscv_assemble(req: RiscvAssembleRequest):
    """Parse and assemble RISC-V source, returning machine words, instruction display rows, and initial registers."""
    rparser = RiscvParser()
    parsed_lines = rparser.parse(req.source)
    if parsed_lines is None:
        errors = [{"line": e.line_number, "message": e.message} for e in rparser.errors]
        raise HTTPException(status_code=400, detail={"errors": errors})

    assembler = RiscvAssembler()
    words = assembler.assemble(parsed_lines, rparser.symbol_table)

    display_lines = _riscv_build_display(parsed_lines, rparser.symbol_table)

    sim = Simulation()
    sim.load(req.source)
    if sim._errors:
        errors = [{"line": e.line_number, "message": e.message} for e in sim._errors]
        raise HTTPException(status_code=400, detail={"errors": errors})

    snap = sim.snapshot()
    return {
        "words":        words,
        "instructions": display_lines,
        "registers":    snap["registers"],
        "halted":       snap["halted"],
    }

@app.post("/api/riscv/step")
def riscv_step(req: RiscvStepRequest):
    """Execute RISC-V source up to step N (stateless).

    Re-simulates from scratch each call: runs N-1 warm-up steps silently,
    then captures PC, registers, halt status, and console output from step N only.
    """
    sim = Simulation()
    sim.load(req.source)
    if sim._errors:
        errors = [{"line": e.line_number, "message": e.message} for e in sim._errors]
        raise HTTPException(status_code=400, detail={"errors": errors})

    # Run warm-up steps (N-1), then capture only the output from the Nth step
    for _ in range(req.step_count - 1):
        if sim.halted:
            break
        sim.step()

    prev_output_len = len(sim._io_output)
    executed_pc = sim.PC          # PC of instruction about to run
    if not sim.halted:
        sim.step()

    snap = sim.snapshot()
    return {
        "PC":          snap["PC"],
        "executed_pc": executed_pc,
        "halted":      snap["halted"],
        "registers":   snap["registers"],
        "io_output":   snap["io_output"][prev_output_len:],
    }
