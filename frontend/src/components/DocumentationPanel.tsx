import React from 'react'

const DocumentationPanel: React.FC = () => (
  <div className="doc-panel">
    <div className="doc-content">

      {/* ── About ─────────────────────────────────────────────── */}
      <section className="doc-section">
        <h1 className="doc-title">AssemblyViz Documentation</h1>
        <p className="doc-lead">
          AssemblyViz is a web-based, step-by-step visualizer for assembly code execution.
          It supports two architectures — <strong>HYMN</strong>, a minimal 8-bit educational CPU,
          and <strong>RISC-V RV32I</strong>, the full 32-bit base integer instruction set.
          Write assembly, assemble it, then step through execution one instruction at a time
          while watching registers and memory update in real time.
        </p>
      </section>

      {/* ── Authors & Acknowledgements ────────────────────────── */}
      <section className="doc-section">
        <h2 className="doc-heading">Authors</h2>
        <p className="doc-authors-inline">
          Nikita Aleksii · Robby Votta · Maria Fajardo · Yurdanur Yolcu
        </p>

        <h3 className="doc-subheading">Acknowledgements</h3>
        <p>
          The HYMN instruction set architecture and its educational design originate from{' '}
          <strong>simHYMN</strong>, created by <strong>Carl Burch</strong> and{' '}
          <strong>Lynn Ziegler</strong> (© 2003).{' '}
          <a
            className="doc-link"
            href="https://cburch.com/socs/hymn/download.html"
            target="_blank"
            rel="noreferrer"
          >
            cburch.com/socs/hymn
          </a>
          . AssemblyViz adapts the HYMN ISA for interactive, browser-based visualization,
          extending it with a two-pass assembler, a REST API step engine, and a full frontend
          debugger with step-back support.
        </p>
      </section>

      {/* ── How to Use ────────────────────────────────────────── */}
      <section className="doc-section">
        <h2 className="doc-heading">How to Use</h2>

        <h3 className="doc-subheading">1. Select an ISA</h3>
        <p>
          Use the <strong>HYMN / RISC-V</strong> toggle in the top-right of the navbar to choose
          your target architecture. Switching ISAs clears all simulation state.
        </p>

        <h3 className="doc-subheading">2. Write or Import Assembly</h3>
        <p>
          The <strong>Editor</strong> tab (left panel) is a plain-text assembly editor with line
          numbers. You can type directly, or use the <strong>Import</strong> button to load a{' '}
          <code>.txt</code> or <code>.s</code> file from disk. The <strong>Export</strong> button
          saves the current editor contents as a <code>.txt</code> file.
        </p>

        <h3 className="doc-subheading">3. Provide Input (HYMN only)</h3>
        <p>
          If your HYMN program uses the <code>READ</code> pseudo-op to read integers from
          the console, enter one value per line in the <strong>Input Queue</strong> box below
          the editor. Values are consumed in order as each <code>READ</code> is executed.
        </p>

        <h3 className="doc-subheading">4. Assemble and Run</h3>
        <p>
          Click <strong>Assemble</strong> to parse and encode your source code. The center
          panel (<em>Results</em>) shows the assembled listing with addresses, machine-code
          words, and decoded mnemonics. Then use the playback controls:
        </p>
        <table className="doc-table">
          <thead><tr><th>Control</th><th>Action</th></tr></thead>
          <tbody>
            <tr><td>◀ Step Back</td><td>Rewind one instruction using the saved snapshot stack</td></tr>
            <tr><td>▶ Play</td><td>Run continuously at the configured speed until halt</td></tr>
            <tr><td>▶| Step Forward</td><td>Execute exactly one instruction</td></tr>
            <tr><td>↺ Reset</td><td>Clear simulation state (editor contents are preserved)</td></tr>
          </tbody>
        </table>

        <h3 className="doc-subheading">5. Control Playback Speed</h3>
        <p>
          The <strong>speed slider</strong> in the navbar sets the delay between automatic steps
          during Play mode, from <strong>0 ms</strong> (as fast as possible) to{' '}
          <strong>1000 ms</strong> (one step per second).
        </p>

        <h3 className="doc-subheading">6. Inspect State</h3>
        <p>
          The <strong>right panel</strong> shows all CPU registers after every step. Use the
          format selector to display values in <em>Hexadecimal</em> or <em>Decimal</em>.
          Switch the left panel to the <strong>Memory</strong> tab to see every memory slot,
          with the active address highlighted in red and changed cells flash-animated.
        </p>
      </section>

      {/* ── HYMN ISA ──────────────────────────────────────────── */}
      <section className="doc-section">
        <h2 className="doc-heading">HYMN Instruction Set Architecture</h2>
        <p>
          HYMN is a minimal 8-bit CPU designed for teaching assembly concepts. Its simplicity
          makes the relationship between source code, machine words, and CPU state immediately
          visible — every instruction fits in a single byte.
        </p>

        <h3 className="doc-subheading">Architecture</h3>
        <table className="doc-table">
          <thead><tr><th>Property</th><th>Value</th></tr></thead>
          <tbody>
            <tr><td>Word size</td><td>8 bits</td></tr>
            <tr><td>Memory</td><td>32 bytes (addresses 0x00–0x1F)</td></tr>
            <tr><td>Registers</td><td>PC, AC, IR</td></tr>
            <tr><td>Status flags</td><td>Zero Flag, Positive Flag (read-only, derived from AC)</td></tr>
          </tbody>
        </table>

        <h3 className="doc-subheading">Registers</h3>
        <table className="doc-table">
          <thead><tr><th>Register</th><th>Full Name</th><th>Description</th></tr></thead>
          <tbody>
            <tr><td><code>PC</code></td><td>Program Counter</td><td>Address of the next instruction to fetch</td></tr>
            <tr><td><code>AC</code></td><td>Accumulator</td><td>General-purpose register; all arithmetic results land here</td></tr>
            <tr><td><code>IR</code></td><td>Instruction Register</td><td>Holds the raw 8-bit word fetched from memory for the current instruction</td></tr>
          </tbody>
        </table>

        <h3 className="doc-subheading">Instruction Encoding</h3>
        <p>
          Every instruction is one byte. The high 3 bits are the opcode and the low 5 bits
          are the operand address:
        </p>
        <pre className="doc-code">{`[ opcode (3 bits) | address (5 bits) ]
  bits 7–5            bits 4–0`}</pre>

        <h3 className="doc-subheading">Instruction Set</h3>
        <table className="doc-table">
          <thead>
            <tr><th>Mnemonic</th><th>Opcode</th><th>Operand</th><th>Effect</th></tr>
          </thead>
          <tbody>
            <tr><td><code>HALT</code></td><td><code>000</code></td><td>—</td><td>Stop the machine</td></tr>
            <tr><td><code>JUMP</code></td><td><code>001</code></td><td>address</td><td>PC = address</td></tr>
            <tr><td><code>JZER</code></td><td><code>010</code></td><td>address</td><td>If AC == 0: PC = address, else PC += 1</td></tr>
            <tr><td><code>JPOS</code></td><td><code>011</code></td><td>address</td><td>If AC &gt; 0: PC = address, else PC += 1</td></tr>
            <tr><td><code>LOAD</code></td><td><code>100</code></td><td>address</td><td>AC = memory[address]; PC += 1</td></tr>
            <tr><td><code>STOR</code></td><td><code>101</code></td><td>address</td><td>memory[address] = AC; PC += 1</td></tr>
            <tr><td><code>ADD</code></td><td><code>110</code></td><td>address</td><td>AC = AC + memory[address]; PC += 1</td></tr>
            <tr><td><code>SUB</code></td><td><code>111</code></td><td>address</td><td>AC = AC − memory[address]; PC += 1</td></tr>
          </tbody>
        </table>

        <h3 className="doc-subheading">Pseudo-ops</h3>
        <p>
          Two pseudo-ops provide I/O support. They expand to real instructions at assembly time
          and are handled by the machine at runtime:
        </p>
        <table className="doc-table">
          <thead><tr><th>Pseudo-op</th><th>Expands to</th><th>Effect</th></tr></thead>
          <tbody>
            <tr><td><code>READ</code></td><td><code>LOAD 30</code></td><td>Read the next integer from the Input Queue into AC</td></tr>
            <tr><td><code>WRITE</code></td><td><code>STOR 31</code></td><td>Write AC to the I/O console output</td></tr>
          </tbody>
        </table>

        <h3 className="doc-subheading">Syntax</h3>
        <ul className="doc-list">
          <li>Mnemonics are case-insensitive (<code>LOAD</code>, <code>load</code>, and <code>Load</code> are equivalent).</li>
          <li>Comments begin with <code>;</code> and extend to the end of the line.</li>
          <li>Labels end with <code>:</code> and can appear on their own line or inline with an instruction.</li>
          <li>Operands are decimal integers or label names.</li>
        </ul>

        <h3 className="doc-subheading">Example — Sum two numbers</h3>
        <pre className="doc-code">{`; Compute A + B and write result to console
        LOAD 10     ; AC = A
        ADD  11     ; AC = AC + B
        WRITE       ; print AC
        HALT

; Data section (manual placement at address 10)
        10          ; A = 10
        5           ; B = 5`}</pre>

        <h3 className="doc-subheading">Example — Loop with conditional branch</h3>
        <pre className="doc-code">{`; Count down from 3 to 0
        LOAD  COUNT     ; AC = 3
LOOP:   WRITE           ; print AC
        SUB   ONE       ; AC = AC - 1
        JZER  DONE      ; if AC == 0, jump to DONE
        JUMP  LOOP      ; else loop
DONE:   HALT

COUNT:  3
ONE:    1`}</pre>
      </section>

      {/* ── RISC-V ISA ────────────────────────────────────────── */}
      <section className="doc-section">
        <h2 className="doc-heading">RISC-V RV32I Instruction Set Architecture</h2>
        <p>
          AssemblyViz implements the full <strong>RV32I base integer instruction set</strong> —
          the 32-bit open-standard RISC architecture. Programs go through a two-pass assembler
          that validates mnemonics, operands, and label references, then encodes each instruction
          into a 32-bit machine word. The simulator re-executes from the beginning on every
          step request, making replay exact and deterministic.
        </p>

        <h3 className="doc-subheading">Architecture</h3>
        <table className="doc-table">
          <thead><tr><th>Property</th><th>Value</th></tr></thead>
          <tbody>
            <tr><td>Word size</td><td>32 bits</td></tr>
            <tr><td>Memory</td><td>Byte-addressable, word-aligned, configurable depth (default 4 096 bytes)</td></tr>
            <tr><td>Registers</td><td>32 general-purpose registers x0–x31 (x0 hardwired to zero)</td></tr>
            <tr><td>Stack pointer</td><td>sp (x2), initialised to top of memory</td></tr>
          </tbody>
        </table>

        <h3 className="doc-subheading">Register File</h3>
        <table className="doc-table">
          <thead><tr><th>Register</th><th>ABI Name</th><th>Convention</th></tr></thead>
          <tbody>
            <tr><td><code>x0</code></td><td><code>zero</code></td><td>Hardwired zero — writes are discarded</td></tr>
            <tr><td><code>x1</code></td><td><code>ra</code></td><td>Return address</td></tr>
            <tr><td><code>x2</code></td><td><code>sp</code></td><td>Stack pointer</td></tr>
            <tr><td><code>x3</code></td><td><code>gp</code></td><td>Global pointer</td></tr>
            <tr><td><code>x4</code></td><td><code>tp</code></td><td>Thread pointer</td></tr>
            <tr><td><code>x5–x7</code></td><td><code>t0–t2</code></td><td>Temporary registers</td></tr>
            <tr><td><code>x8</code></td><td><code>s0 / fp</code></td><td>Saved register / frame pointer</td></tr>
            <tr><td><code>x9</code></td><td><code>s1</code></td><td>Saved register</td></tr>
            <tr><td><code>x10–x11</code></td><td><code>a0–a1</code></td><td>Function arguments / return values</td></tr>
            <tr><td><code>x12–x17</code></td><td><code>a2–a7</code></td><td>Function arguments / syscall number (a7)</td></tr>
            <tr><td><code>x18–x27</code></td><td><code>s2–s11</code></td><td>Saved registers</td></tr>
            <tr><td><code>x28–x31</code></td><td><code>t3–t6</code></td><td>Temporary registers</td></tr>
          </tbody>
        </table>

        <h3 className="doc-subheading">Instruction Formats</h3>
        <table className="doc-table">
          <thead><tr><th>Format</th><th>Instructions</th></tr></thead>
          <tbody>
            <tr><td>R-type</td><td><code>add sub and or xor sll srl sra slt sltu</code></td></tr>
            <tr><td>I-type (arithmetic)</td><td><code>addi andi ori xori slti sltiu slli srli srai</code></td></tr>
            <tr><td>Load</td><td><code>lw lh lb lhu lbu</code></td></tr>
            <tr><td>Store</td><td><code>sw sh sb</code></td></tr>
            <tr><td>Branch</td><td><code>beq bne blt bge bltu bgeu</code></td></tr>
            <tr><td>U-type</td><td><code>lui auipc</code></td></tr>
            <tr><td>Jump</td><td><code>jal jalr</code></td></tr>
            <tr><td>System</td><td><code>ecall ebreak</code></td></tr>
          </tbody>
        </table>

        <h3 className="doc-subheading">Pseudo-instructions</h3>
        <table className="doc-table">
          <thead><tr><th>Pseudo</th><th>Expands to</th></tr></thead>
          <tbody>
            <tr><td><code>li rd, imm</code></td><td><code>addi rd, x0, imm</code> (small) or <code>lui</code> + <code>addi</code> (large)</td></tr>
            <tr><td><code>la rd, symbol</code></td><td><code>lui rd, %hi(addr)</code> + <code>addi rd, rd, %lo(addr)</code></td></tr>
            <tr><td><code>mv rd, rs</code></td><td><code>addi rd, rs, 0</code></td></tr>
            <tr><td><code>j label</code></td><td><code>jal x0, offset</code></td></tr>
            <tr><td><code>ret</code></td><td><code>jalr x0, ra, 0</code></td></tr>
            <tr><td><code>nop</code></td><td><code>addi x0, x0, 0</code></td></tr>
          </tbody>
        </table>

        <h3 className="doc-subheading">Syscall Convention</h3>
        <p>
          Load the syscall number into <code>a7</code>, arguments into <code>a0</code>–<code>a6</code>,
          then execute <code>ecall</code>:
        </p>
        <table className="doc-table">
          <thead><tr><th>a7</th><th>Operation</th></tr></thead>
          <tbody>
            <tr><td><code>1</code></td><td>Print integer in <code>a0</code> to console</td></tr>
            <tr><td><code>4</code></td><td>Print null-terminated string at address in <code>a0</code></td></tr>
            <tr><td><code>10</code></td><td>Exit — halts the simulation</td></tr>
          </tbody>
        </table>

        <h3 className="doc-subheading">Memory Layout</h3>
        <pre className="doc-code">{`Address 0x0000  ┌──────────────────────┐
                │   .text              │  instructions
                ├──────────────────────┤
                │   .data              │  .word / .asciz values
                └──────────────────────┘
                  stack pointer (sp) starts at top, grows down ↓`}</pre>

        <h3 className="doc-subheading">Example — Add two numbers</h3>
        <pre className="doc-code">{`.text
main:
    li   a0, 10       # a0 = 10
    li   a1, 25       # a1 = 25
    add  a0, a0, a1   # a0 = a0 + a1 = 35
    li   a7, 1        # syscall: print int
    ecall
    li   a7, 10       # syscall: exit
    ecall`}</pre>

        <h3 className="doc-subheading">Example — Loop</h3>
        <pre className="doc-code">{`.text
main:
    li   t0, 0        # counter = 0
    li   t1, 5        # limit = 5
loop:
    bge  t0, t1, done # if counter >= 5, exit
    mv   a0, t0       # a0 = counter
    li   a7, 1        # print int
    ecall
    addi t0, t0, 1    # counter++
    j    loop
done:
    li   a7, 10
    ecall`}</pre>
      </section>

    </div>
  </div>
)

export default DocumentationPanel
