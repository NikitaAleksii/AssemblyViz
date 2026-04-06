import React from 'react'
import { MemorySlot, DisplayFormat } from '../types'

interface MemoryPanelProps {
  slots: MemorySlot[]
  displayFormat: DisplayFormat
  onFormatChange: (fmt: DisplayFormat) => void
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
          <span>INSTRUCTION</span>
        </div>
        <div className="memory-body">
          {slots.map((slot, idx) => (
            <div
              key={idx}
              className={`memory-row ${slot.isActive ? 'active-row' : ''}`}
            >
              <span className="memory-address">{slot.address}</span>
              <span className="memory-instruction">{slot.instruction}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default MemoryPanel
