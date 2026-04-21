import React from 'react'
import { ISAMode } from '../types'
import logo from '../assets/logo.svg'
import backwards from '../assets/backwards.svg'
import forward from '../assets/forward.svg'
import play from '../assets/play.svg'
import reset from '../assets/reset.svg'

/** Props for the Navbar component. */
interface NavbarProps {
  activeTab: 'editor' | 'memory'
  /** Callback invoked when the user switches between Editor and Memory tabs. */
  onTabChange: (tab: 'editor' | 'memory') => void
  isaMode: ISAMode
  /** Callback invoked when the user toggles the ISA mode. */
  onISAChange: (mode: ISAMode) => void
  speedMs: number
  /** Callback invoked when the user adjusts the speed slider. */
  onSpeedChange: (ms: number) => void
  /** Step the simulation one instruction backward. */
  onBack: () => void
  /** Start or resume automatic playback. */
  onPlay: () => void
  /** Step the simulation one instruction forward. */
  onStep: () => void
  /** Reset the simulation to its initial state. */
  onReset: () => void
}

/**
 * Navbar renders the application's top bar, containing:
 * - The AssemblyViz logo
 * - Editor / Memory view tabs
 * - Playback controls (back, play, step, reset)
 * - A speed slider that controls the auto-play step delay
 * - An ISA mode toggle (HYMN vs RISC-V)
 */
const Navbar: React.FC<NavbarProps> = ({
  activeTab, onTabChange,
  isaMode, onISAChange,
  speedMs, onSpeedChange,
  onBack, onPlay, onStep, onReset,
}) => {
  return (
    <header className="topbar">

      {/* Logo imported from the Figma export */}
      <div className="logo">
        <img src={logo} alt="AssemblyViz" height="28" />
      </div>

      {/* View tabs — active tab receives the "active" class for highlighted styling */}
      <div className="top-tabs">
        <button
          className={`tab ${activeTab === 'editor' ? 'active' : ''}`}
          onClick={() => onTabChange('editor')}
        >
          &lt;/&gt; Editor
        </button>
        <button
          className={`tab ${activeTab === 'memory' ? 'active' : ''}`}
          onClick={() => onTabChange('memory')}
        >
          ☰ Memory
        </button>
      </div>

      {/* Playback controls: back, play, step, reset (SVG icons) */}
      <div className="top-controls">
        <button className="ctrl-btn" onClick={onBack}  title="Step Back">
          <img src={backwards} alt="Step Back" height="24" />
        </button>
        <button className="ctrl-btn" onClick={onPlay}  title="Play">
          <img src={play} alt="Play" height="24" />
        </button>
        <button className="ctrl-btn" onClick={onStep}  title="Step Forward">
          <img src={forward} alt="Step Forward" height="24" />
        </button>
        <button className="ctrl-btn" onClick={onReset} title="Reset">
          <img src={reset} alt="Reset" height="30" />
        </button>
      </div>

      {/* Speed slider — range 0–1000 ms in 50 ms increments; label shows current value */}
      <div className="speed-control">
        <input
          type="range"
          min={0} max={1000} step={50}
          value={speedMs}
          onChange={e => onSpeedChange(Number(e.target.value))}
        />
        <span className="speed-label">{speedMs} ms</span>
      </div>

      {/* ISA toggle — switches the simulator between HYMN and RISC-V assembly dialects */}
      <div className="mode-switch">
        <button className={`mode ${isaMode === 'HYMN'   ? 'active' : ''}`} onClick={() => onISAChange('HYMN')}>HYMN</button>
        <button className={`mode ${isaMode === 'RISC-V' ? 'active' : ''}`} onClick={() => onISAChange('RISC-V')}>RISC-V</button>
      </div>
    </header>
  )
}

export default Navbar
