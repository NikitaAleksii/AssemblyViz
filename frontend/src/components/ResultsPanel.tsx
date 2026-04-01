import React from 'react'
import { AssembledInstruction } from '../types'

interface ResultsPanelProps {
  instructions: AssembledInstruction[]
  onExportResults: () => void
}

const ResultsPanel: React.FC<ResultsPanelProps> = ({ instructions, onExportResults }) => {
  return (
    <section className="center-panel">
      <div className="panel-header">
        <h2>RESULTS</h2>
        <button onClick={onExportResults}>EXPORT CODE</button>
      </div>

      <div className="results-box">
        <div className="results-header">
          <span>ADDRESS</span>
          <span>CODE</span>
          <span>INSTRUCTION</span>
        </div>

        <div className="results-body">
          {instructions.map((instr, idx) => (
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
