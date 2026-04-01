import React from 'react'
import { ISAMode } from '../types'

interface NavbarProps {
  activeTab: 'editor' | 'memory'
  onTabChange: (tab: 'editor' | 'memory') => void
  isaMode: ISAMode
  onISAChange: (mode: ISAMode) => void
  speedMs: number
  onSpeedChange: (ms: number) => void
  onBack: () => void
  onPlay: () => void
  onStep: () => void
  onReset: () => void
}

const Navbar: React.FC<NavbarProps> = ({
  activeTab, onTabChange,
  isaMode, onISAChange,
  speedMs, onSpeedChange,
  onBack, onPlay, onStep, onReset,
}) => {
  return (
    <header className="topbar">

      {/* Logo — styled "A" + "ssemblyViz" */}
      <div className="logo">
        <span className="logo-a">A</span>
        <span className="logo-rest">ssemblyViz</span>
      </div>

      {/* View tabs with icons */}
      <div className="top-tabs">
        <button
          className={`tab ${activeTab === 'editor' ? 'active' : ''}`}
          onClick={() => onTabChange('editor')}
        >
          <span className="tab-icon">&lt;/&gt;</span> Editor
        </button>
        <button
          className={`tab ${activeTab === 'memory' ? 'active' : ''}`}
          onClick={() => onTabChange('memory')}
        >
          <span className="tab-icon">☰</span> Memory
        </button>
      </div>

      {/* Playback controls — outline triangle style */}
      <div className="top-controls">
        <button className="ctrl-btn" onClick={onBack}  title="Step Back">&#9665;</button>
        <button className="ctrl-btn" onClick={onPlay}  title="Play">&#9655;</button>
        <button className="ctrl-btn" onClick={onStep}  title="Step Forward">&#9655;&#9655;</button>
        <button className="ctrl-btn" onClick={onReset} title="Reset">&#8635;</button>
      </div>

      {/* Speed slider */}
      <div className="speed-control">
        <input
          type="range"
          min={50} max={1000} step={50}
          value={speedMs}
          onChange={e => onSpeedChange(Number(e.target.value))}
        />
        <span className="speed-label">{speedMs} ms</span>
      </div>

      {/* ISA toggle */}
      <div className="mode-switch">
        <button
          className={`mode ${isaMode === 'HYMN' ? 'active' : ''}`}
          onClick={() => onISAChange('HYMN')}
        >
          HYMN
        </button>
        <button
          className={`mode ${isaMode === 'RISC-V' ? 'active' : ''}`}
          onClick={() => onISAChange('RISC-V')}
        >
          RISC-V
        </button>
      </div>
    </header>
  )
}

export default Navbar
