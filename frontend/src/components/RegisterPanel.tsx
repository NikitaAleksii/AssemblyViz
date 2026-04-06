import React from 'react'
import { Register, DisplayFormat } from '../types'

interface RegisterPanelProps {
  registers: Register[]
  displayFormat: DisplayFormat
  onFormatChange: (fmt: DisplayFormat) => void
}

function formatValue(reg: Register, fmt: DisplayFormat): string {
  if (typeof reg.value === 'string') return reg.value
  const num = Number(reg.value)
  if (fmt === 'DECIMAL') return String(num)
  if (fmt === 'INSTRUCTION') return String(num) // placeholder until backend provides instruction strings
  // HEXADECIMAL — pad to 8 chars for RISC-V style
  return '0x' + num.toString(16).padStart(8, '0').toUpperCase()
}

const RegisterPanel: React.FC<RegisterPanelProps> = ({
  registers, displayFormat, onFormatChange,
}) => {
  const isLarge = registers.length > 3  // RISC-V has 32

  return (
    <section className="right-panel">
      <div className="panel-header">
        <h2>REGISTER</h2>
        <select
          className="format-select"
          value={displayFormat}
          onChange={e => onFormatChange(e.target.value as DisplayFormat)}
        >
          <option value="HEXADECIMAL">HEXADECIMAL</option>
          <option value="DECIMAL">DECIMAL</option>
          <option value="INSTRUCTION">INSTRUCTION</option>
        </select>
      </div>

      <div className="register-box">
        <div className="register-header">
          <span>NAME</span>
          <span>NUMBER</span>
          <span>VALUE</span>
        </div>
        <div className="register-body">
          {registers.map(reg => (
            <div
              key={reg.name}
              className={`register-row ${isLarge ? 'register-row--sm' : ''}`}
            >
              <span>{reg.name}</span>
              <span>{reg.number}</span>
              <span>{formatValue(reg, displayFormat)}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default RegisterPanel
