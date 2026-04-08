import React from 'react'
import { MemorySlot, DisplayFormat } from '../types'

interface MemoryPanelProps {
  slots: MemorySlot[]
  displayFormat: DisplayFormat
  onFormatChange: (fmt: DisplayFormat) => void
}

function formatSlot(slot: MemorySlot, fmt: DisplayFormat): string {
  if (fmt === 'INSTRUCTION' || slot.value === undefined) return slot.instruction
  const isRISCV = slot.address.startsWith('0x')
  if (fmt === 'HEXADECIMAL') {
    const hex = (slot.value >>> 0).toString(16).toUpperCase()
    return isRISCV ? `0x${hex.padStart(8, '0')}` : `0x${hex.padStart(2, '0')}`
  }
  // DECIMAL
  return slot.value.toString()
}

const MemoryPanel: React.FC<MemoryPanelProps> = ({ slots, displayFormat, onFormatChange }) => {
  return (
    <section className="left-panel">
      <div className="panel-header">
        <h2>MEMORY</h2>
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

      <div className="memory-table-wrap">
        <div className="memory-header">
          <span>ADDRESS</span>
          <span>{displayFormat === 'INSTRUCTION' ? 'INSTRUCTION' : 'VALUE'}</span>
        </div>
        <div className="memory-body">
          {slots.map((slot, idx) => (
            <div
              key={idx}
              className={`memory-row ${slot.isActive ? 'active-row' : ''} ${slot.isChanged ? 'changed-row' : ''}`}
            >
              <span className="memory-address">{slot.address}</span>
              <span className="memory-instruction">{formatSlot(slot, displayFormat)}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default MemoryPanel
