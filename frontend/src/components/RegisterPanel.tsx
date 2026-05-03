import React from 'react'
import { Register, DisplayFormat } from '../types'

const HYMN_OPCODES: Record<number, string> = {
  0: 'HALT', 1: 'JUMP', 2: 'JZER', 3: 'JPOS',
  4: 'LOAD', 5: 'STOR', 6: 'ADD',  7: 'SUB',
}

function decodeIR(value: number): string {
  const opcode = (value >> 5) & 0b111
  const address = value & 0b11111
  return `${HYMN_OPCODES[opcode] ?? '???'} ${address.toString(2).padStart(5, '0')}`
}

/** Props for the RegisterPanel component. */
interface RegisterPanelProps {
  /** List of registers to display (3 for HYMN, 32 for RISC-V). */
  registers: Register[]
  displayFormat: DisplayFormat
  /** Callback invoked when the user selects a new display format. */
  onFormatChange: (fmt: DisplayFormat) => void
}

/**
 * Formats a register's value according to the selected display format.
 *
 * - String values (e.g. symbolic placeholders) are returned as-is.
 * - DECIMAL: returns the numeric value as a plain decimal string.
 * - HEXADECIMAL: returns the unsigned 32-bit hex representation, zero-padded
 *   to 8 digits and prefixed with "0x".
 *
 * The `>>> 0` coercion ensures negative JS numbers are treated as unsigned
 * 32-bit integers before hex conversion.
 */
function formatValue(reg: Register, fmt: DisplayFormat): string {
  if (typeof reg.value === 'string') return reg.value
  const num = Number(reg.value)
  if (fmt === 'DECIMAL') return String(num)
  return '0x' + (num >>> 0).toString(16).padStart(8, '0').toUpperCase()
}

/**
 * RegisterPanel displays a table of CPU registers with their ABI names,
 * register numbers, and current values.
 *
 * Layout adapts to the ISA: HYMN has 3 registers (normal row size) while
 * RISC-V has 32 registers (compact rows with "x0"–"x31" numbering).
 * The user can switch value display between hexadecimal and decimal via the
 * format selector in the panel header.
 */
const RegisterPanel: React.FC<RegisterPanelProps> = ({
  registers, displayFormat, onFormatChange,
}) => {
  // Use compact row styling when there are more than 3 registers (i.e. RISC-V).
  const isLarge = registers.length > 5

  return (
    <section className="right-panel">
      <div className="panel-header">
        <h2>REGISTERS</h2>

        {/* Format selector — INSTRUCTION is not applicable to registers, so only
            HEXADECIMAL and DECIMAL are offered here (unlike the MemoryPanel). */}
        <select
          className="format-select"
          value={displayFormat}
          onChange={e => onFormatChange(e.target.value as DisplayFormat)}
        >
          <option value="HEXADECIMAL">HEXADECIMAL</option>
          <option value="DECIMAL">DECIMAL</option>
        </select>
      </div>

      <div className="register-box">
        {/* Column headers: ABI name, register index, formatted value */}
        <div className="register-header">
          <span>ABI</span>
          <span>REG</span>
          <span>VALUE</span>
        </div>

        <div className="register-body">
          {registers.map(reg => (
            <div
              key={reg.name}
              className={`register-row ${isLarge ? 'register-row--sm' : ''}`}
            >
              {/* ABI name (e.g. "zero", "ra", "sp" for RISC-V) */}
              <span>{reg.name}</span>
              {/* Register number — prefixed with "x" for RISC-V (x0–x31) */}
              <span>{isLarge ? `x${reg.number}` : reg.number}</span>
              <span>{(reg.name == 'IR' && !isLarge) ? decodeIR(reg.value as number) :
                     formatValue(reg, displayFormat)}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default RegisterPanel
