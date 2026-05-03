# Testing 

## Running the HYMN Tests

One test per module:

- `test_instructions.py` — register completeness, opcode ranges, immutability
- `test_parser.py` — tokenization, label resolution, encoding, full integration
- `test_machine.py` — all instructions, register behavior, memory, encode/decode
- `test_executor.py` — load, step, run, reset, state inspection
- `test_debugger.py` — breakpoint management, step, run_until_break

Run them with:

```bash
cd test
pytest hymn
```

### Manual Testing

Along with pytest, assembly programs from previous Computer Organization's (CSC250) homework assignments were run through this implementation and compared to the SimHYMN reference.

Programs used:

- `sumn.s` — takes an input number n and returns the sum of 0 through n
- `mult.s` — multiplies two input numbers
- `primes.s` — prints the first 12 prime numbers
- `virus.s` — copies its own code into memory

Each program was first run in the SimHYMN reference to record the final AC value, final memory contents, I/O output, and PC value at halt. The same programs were then run through this implementation and the outputs were compared to verify correctness.

---

## Running the RISC-V Tests

One test per module:

- `assembler_test.py` — assembly code to machine instruction conversion
- `decoder_test.py` — machine instruction decoding into constituent fields
- `memory_test.py` — memory encoding and addressing
- `parser_test.py` — two-pass parsing: error extraction and line tokenization
- `simulation_test.py` — instruction execution, register state, and memory state

Run them with:

```bash
cd test
pytest riscv
```

```bash
cd test
python3 -m riscv.simulation_test
```