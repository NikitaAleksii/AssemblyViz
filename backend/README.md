# Backend

FastAPI server that bridges the React frontend with the Python assembler and simulator engines for two instruction set architectures: **HYMN** (8-bit educational ISA) and **RISC-V** (RV32I).

---

## Structure

```text
backend/
├── __init__.py
├── main.py          # FastAPI app — all HTTP endpoints
├── hymn/            # HYMN 8-bit assembler and simulator
└── riscv/           # RISC-V RV32I assembler and simulator
```

See [hymn/README.md](hymn/README.md) and [riscv/README.md](riscv/README.md) for details on each engine.

---

## Setup

Python 3.10+ is required. Install dependencies:

```bash
pip install -r requirements.txt
```

Start the server from the `backend/` directory:

```bash
uvicorn main:app --reload
```

The server runs on `http://localhost:8000`. CORS origins are configured via the `ALLOWED_ORIGINS` environment variable (comma-separated list). Defaults to `http://localhost:5173` when the variable is not set.

---

## API

The backend is **stateless** — machine state is reconstructed from the data sent by the frontend on every request.

### HYMN

#### `POST /api/hymn/assemble`

Parse and assemble HYMN source code.

**Request**

```json
{ "source": "LOAD 10\nADD 11\nSTOR 12\nHALT" }
```

**Response**

```json
{
  "words":        [138, ...],
  "instructions": [{"address": "00000", "code": "10001010", "instruction": "LOAD 10"}, ...],
  "memory":       [{"address": "00000", "value": 138, "decoded": "LOAD 10"}, ...],
  "registers":    {"pc": 0, "ac": 0, "ir": 0, "zero_flag": "false", "positive_flag": "false", "halted": false}
}
```

Returns `400` with `{"errors": [{"line": N, "message": "..."}]}` on parse failure.

---

#### `POST /api/hymn/step`

Execute one HYMN instruction. The frontend sends the full current machine state; the backend reconstructs it, runs one step, and returns the updated state.

**Request**

```json
{
  "memory":   [0, 0, ..., 0],
  "pc":       0,
  "ac":       0,
  "io_input": 0
}
```

`memory` must be exactly 32 integers. `io_input` supplies the value consumed by the `READ` pseudo-op.

**Response**

```json
{
  "pc":            1,
  "ac":            0,
  "ir":            138,
  "zero_flag":     "false",
  "positive_flag": "false",
  "halted":        false,
  "memory":        [{"address": "00000", "value": 138, "decoded": "LOAD 10"}, ...],
  "io_output":     ""
}
```

---

### RISC-V

#### `POST /api/riscv/assemble`

Parse and assemble RISC-V source code.

**Request**

```json
{ "source": "addi t0, x0, 5\naddi t1, x0, 3\nadd t2, t0, t1" }
```

**Response**

```json
{
  "words":        [293, ...],
  "instructions": [{"address": "0x00000000", "code": "0x00500293", "instruction": "addi t0, x0, 5"}, ...],
  "registers":    [{"index": 0, "names": "zero", "value": 0}, ...],
  "halted":       false
}
```

Pseudo-instructions that expand to multiple machine words have continuation rows marked with `↳`.

Returns `400` with `{"errors": [...]}` on parse failure.

---

#### `POST /api/riscv/step`

Re-simulate from scratch up to step N and return the state at that step. Because the RISC-V engine is stateless, the full source is re-assembled and N−1 warm-up steps are executed silently before capturing the Nth step's output.

**Request**

```json
{
  "source":     "addi t0, x0, 5\n...",
  "step_count": 3
}
```

**Response**

```json
{
  "PC":          8,
  "executed_pc": 8,
  "halted":      false,
  "registers":   [{"index": 0, "names": "zero", "value": 0}, ...],
  "io_output":   ""
}
```
