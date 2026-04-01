import React from 'react'
import { Register, DisplayFormat } from '../types'

interface RegisterPanelProps {
  registers: Register[]
  displayFormat: DisplayFormat
  onFormatChange: (fmt: DisplayFormat) => void
}

/** Format a register value based on selected display format */
function formatValue(reg: Register, fmt: DisplayFormat): string {
  // IR holds instruction names (strings), always show as-is
  if (reg.name === 'IR' && typeof reg.value === 'string') return reg.value

  const num = Number(reg.value)
  if (fmt === 'DECIMAL') return String(num)
  if (fmt === 'BINARY') return '0b' + num.toString(2)
  return '0x' + num.toString(16).toUpperCase() // HEXADECIMAL
}

const RegisterPanel: React.FC<RegisterPanelProps> = ({
  registers, displayFormat, onFormatChange,
}) => {
  return (
    <section className="right-panel">
      <div className="panel-header">
        <h2>REGISTER</h2>
        <select
          value={displayFormat}
          onChange={e => onFormatChange(e.target.value as DisplayFormat)}
        >
          <option value="HEXADECIMAL">HEXADECIMAL</option>
          <option value="DECIMAL">DECIMAL</option>
          <option value="BINARY">BINARY</option>
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
            <div key={reg.name} className="register-row">
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
