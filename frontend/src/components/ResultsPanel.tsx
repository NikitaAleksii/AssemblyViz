import React from 'react'
import { AssembledInstruction } from '../types'

/** Props for the ResultsPanel component. */
interface ResultsPanelProps {
  instructions: AssembledInstruction[]
  /** Callback invoked when the user clicks "EXPORT CODE". */
  onExportResults: () => void
}

/**
 * ResultsPanel displays the assembled output of the current program as a
 * three-column table: memory address, machine code word, and the original
 * instruction mnemonic.
 *
 * The row corresponding to the currently executing instruction is highlighted
 * with the `active-row` class so the user can track the program counter.
 * An "EXPORT CODE" button lets the user download or copy the assembled output.
 */
const ResultsPanel: React.FC<ResultsPanelProps> = ({ instructions, onExportResults }) => {
  return (
    <section className="center-panel">
      <div className="panel-header">
        <h2>RESULTS</h2>
        {/* Exports the assembled instruction list (e.g. as a file download) */}
        <button onClick={onExportResults}>EXPORT CODE</button>
      </div>

      <div className="results-box">
        {/* Column headers: address in memory, encoded machine code, source mnemonic */}
        <div className="results-header">
          <span>ADDRESS</span>
          <span>CODE</span>
          <span>INSTRUCTION</span>
        </div>

        <div className="results-body">
          {instructions.map((instr, idx) => (
            // "active-row" highlights the instruction at the current program counter
            <div
              key={idx}
              className={`results-row ${instr.isActive ? 'active-row' : ''}`}
            >
              <span>{instr.address}</span>
              <span>{instr.code}</span>
              <span>{instr.instruction}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default ResultsPanel
