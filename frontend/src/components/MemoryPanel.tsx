import React from 'react'
import { MemorySlot, DisplayFormat } from '../types'

/** Props for the MemoryPanel component. */
interface MemoryPanelProps {
  slots: MemorySlot[]
  displayFormat: DisplayFormat
  /** Callback invoked when the user selects a new display format. */
  onFormatChange: (fmt: DisplayFormat) => void
}

/**
 * Formats a memory slot's value according to the selected display format.
 *
 * - INSTRUCTION: returns the raw instruction string regardless of numeric value.
 * - HEXADECIMAL: returns the unsigned 32-bit hex representation, zero-padded to
 *   8 digits for RISC-V addresses (0x-prefixed) or 2 digits for others.
 * - DECIMAL: returns the numeric value as a plain decimal string.
 *
 * If the slot has no value, falls back to the instruction string.
 */
function formatSlot(slot: MemorySlot, fmt: DisplayFormat): string {
  if (fmt === 'INSTRUCTION' || slot.value === undefined) return slot.instruction

  // RISC-V addresses use a "0x" prefix; classic addresses do not.
  const isRISCV = slot.address.startsWith('0x')

  if (fmt === 'HEXADECIMAL') {
    // `>>> 0` coerces to an unsigned 32-bit integer before converting to hex.
    const hex = (slot.value >>> 0).toString(16).toUpperCase()
    return isRISCV ? `0x${hex.padStart(8, '0')}` : `0x${hex.padStart(2, '0')}`
  }

  // DECIMAL
  return slot.value.toString()
}

/**
 * MemoryPanel displays a scrollable table of memory slots with their addresses
 * and values. The user can switch the value display format between hexadecimal,
 * decimal, and raw instruction text via the format selector in the panel header.
 *
 * Active (program-counter) rows are highlighted with the `active-row` class;
 * recently-written rows are highlighted with `changed-row`.
 */
const MemoryPanel: React.FC<MemoryPanelProps> = ({ slots, displayFormat, onFormatChange }) => {
  return (
    <section className="left-panel">
      <div className="panel-header">
        <h2>MEMORY</h2>

        {/* Format selector — controls how slot values are rendered */}
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
        {/* Column headers — second column label reflects the active format */}
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
