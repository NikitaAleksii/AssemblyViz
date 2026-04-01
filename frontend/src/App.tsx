import { useState, useEffect, useRef } from 'react'
import Navbar from './components/Navbar'
import CodeEditor from './components/CodeEditor'
import ResultsPanel from './components/ResultsPanel'
import RegisterPanel from './components/RegisterPanel'
import { AssembledInstruction, Register, ISAMode, DisplayFormat } from './types'
import './App.css'

// ─── Default Registers ────────────────────────────────────────────────────────
const DEFAULT_REGISTERS: Register[] = [
  { name: 'PC', number: 0, value: 0 },
  { name: 'IR', number: 1, value: 0 },
  { name: 'AC', number: 2, value: 0 },
]

function App() {
  // ── State (mirrors all the `let` variables in the old script.js) ──
  const [code, setCode]               = useState('')
  const [output, setOutput]           = useState('')
  const [isError, setIsError]         = useState(false)
  const [isaMode, setISAMode]         = useState<ISAMode>('HYMN')
  const [speedMs, setSpeedMs]         = useState(200)
  const [activeTab, setActiveTab]     = useState<'editor' | 'memory'>('editor')
  const [displayFormat, setFormat]    = useState<DisplayFormat>('HEXADECIMAL')
  const [assembled, setAssembled]     = useState<AssembledInstruction[]>([])
  const [registers, setRegisters]     = useState<Register[]>(DEFAULT_REGISTERS)
  const [currentStep, setCurrentStep] = useState(-1)

  const runTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  // ── Helpers ───────────────────────────────────────────────────────
  function showOutput(msg: string, error = false) {
    setOutput(msg)
    setIsError(error)
  }

  function stopRun() {
    if (runTimer.current) {
      clearInterval(runTimer.current)
      runTimer.current = null
    }
  }

  /** Parse non-empty lines from the editor */
  function getCleanLines(src: string) {
    return src
      .split('\n')
      .map((raw, i) => ({ raw, trimmed: raw.trim(), idx: i }))
      .filter(l => l.trimmed !== '')
  }

  /** Update registers to reflect the current step */
  function buildRegisters(step: number, lines: AssembledInstruction[]): Register[] {
    if (step < 0 || step >= lines.length) return [...DEFAULT_REGISTERS]
    const instr = lines[step].instruction
    return [
      { name: 'PC', number: 0, value: step },
      { name: 'IR', number: 1, value: instr.slice(0, 8).toUpperCase() },
      { name: 'AC', number: 2, value: (step + 1) * 8 },
    ]
  }

  // ── Assemble ─────────────────────────────────────────────────────
  function handleAssemble(): boolean {
    stopRun()
    const trimmed = code.trim()

    if (!trimmed) {
      setAssembled([])
      setCurrentStep(-1)
      setRegisters([...DEFAULT_REGISTERS])
      showOutput('Cannot assemble empty code.', true)
      return false
    }

    const lines = getCleanLines(code)
    if (lines.length === 0) {
      showOutput('No valid lines found.', true)
      return false
    }

    // TODO: swap this placeholder with a real call to the backend parser
    // e.g. const result = await fetch('/api/assemble', { method:'POST', body: code })
    const newAssembled: AssembledInstruction[] = lines.map((l, i) => ({
      address: `0x${String(i).padStart(4, '0')}`,
      code: isaMode === 'HYMN'
        ? `H${String(i).padStart(3, '0')}`
        : `R${String(i).padStart(3, '0')}`,
      instruction: l.trimmed,
      isActive: false,
    }))

    setAssembled(newAssembled)
    setCurrentStep(-1)
    setRegisters([...DEFAULT_REGISTERS])
    showOutput(`Assembled ${newAssembled.length} line(s) in ${isaMode} mode.`)
    return true
  }

  // ── Step helpers (operate on the latest state via updater fns) ───
  function doStep(
    prev: AssembledInstruction[],
    prevStep: number,
    direction: 'forward' | 'back'
  ): { next: number; lines: AssembledInstruction[] } {
    let next = direction === 'forward'
      ? Math.min(prevStep + 1, prev.length - 1)
      : Math.max(prevStep - 1, -1)

    const lines = prev.map((l, i) => ({ ...l, isActive: i === next }))
    return { next, lines }
  }

  // ── Step Forward ─────────────────────────────────────────────────
  function handleStep() {
    let lines = assembled
    let step  = currentStep

    if (lines.length === 0) {
      const ok = handleAssemble()
      if (!ok) return
      // After assemble, state updates are async — just start at 0
      return
    }

    if (step >= lines.length - 1) {
      stopRun()
      showOutput('Reached the end of the program.')
      return
    }

    const next    = step + 1
    const updated = lines.map((l, i) => ({ ...l, isActive: i === next }))
    setAssembled(updated)
    setCurrentStep(next)
    setRegisters(buildRegisters(next, updated))
    showOutput(`Step ${next + 1}: ${updated[next].instruction}`)
  }

  // ── Step Back ────────────────────────────────────────────────────
  function handleBack() {
    stopRun()
    if (assembled.length === 0) { showOutput('Nothing to go back through.', true); return }

    const next    = Math.max(currentStep - 1, -1)
    const updated = assembled.map((l, i) => ({ ...l, isActive: i === next }))
    setAssembled(updated)
    setCurrentStep(next)
    setRegisters(buildRegisters(next, updated))

    if (next < 0) showOutput('Returned to start.')
    else showOutput(`Moved back to step ${next + 1}: ${updated[next].instruction}`)
  }

  // ── Play (auto-run) ──────────────────────────────────────────────
  function handlePlay() {
    if (assembled.length === 0) {
      const ok = handleAssemble()
      if (!ok) return
    }
    stopRun()
    showOutput('Running program...')
    runTimer.current = setInterval(() => {
      // Use functional updates so we always get fresh state inside the interval
      setCurrentStep(prev => {
        setAssembled(lines => {
          const next = prev + 1
          if (next >= lines.length) {
            stopRun()
            showOutput('Run complete.')
            return lines
          }
          const updated = lines.map((l, i) => ({ ...l, isActive: i === next }))
          setRegisters(buildRegisters(next, updated))
          showOutput(`Step ${next + 1}: ${updated[next].instruction}`)
          return updated
        })
        return prev + 1 < assembled.length ? prev + 1 : prev
      })
    }, speedMs)
  }

  // ── Reset ────────────────────────────────────────────────────────
  function handleReset() {
    stopRun()
    setCode('')
    setAssembled([])
    setCurrentStep(-1)
    setRegisters([...DEFAULT_REGISTERS])
    showOutput('Editor and results reset.')
  }

  // ── Export editor text ───────────────────────────────────────────
  function handleExport() {
    if (!code.trim()) { showOutput('Nothing to export.', true); return }
    const blob = new Blob([code], { type: 'text/plain' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url; a.download = 'assembly-code.txt'; a.click()
    URL.revokeObjectURL(url)
    showOutput('Editor code exported.')
  }

  // ── Export results table ─────────────────────────────────────────
  function handleExportResults() {
    if (assembled.length === 0) { showOutput('No results to export.', true); return }
    const text = assembled
      .map(l => `${l.address}    ${l.code}    ${l.instruction}`)
      .join('\n')
    const blob = new Blob([text], { type: 'text/plain' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url; a.download = 'assembly-results.txt'; a.click()
    URL.revokeObjectURL(url)
    showOutput('Results exported.')
  }

  // ── Cleanup interval on unmount ──────────────────────────────────
  useEffect(() => () => stopRun(), [])

  // ── ISA mode change: update placeholder output ───────────────────
  function handleISAChange(mode: ISAMode) {
    setISAMode(mode)
    showOutput(`${mode} mode selected.`)
  }

  // ── Tab change ───────────────────────────────────────────────────
  function handleTabChange(tab: 'editor' | 'memory') {
    setActiveTab(tab)
    if (tab === 'memory') showOutput('Memory tab selected.')
    else showOutput('Editor tab selected.')
  }

  return (
    <div className="app-shell">
      <Navbar
        activeTab={activeTab}       onTabChange={handleTabChange}
        isaMode={isaMode}           onISAChange={handleISAChange}
        speedMs={speedMs}           onSpeedChange={setSpeedMs}
        onBack={handleBack}         onPlay={handlePlay}
        onStep={handleStep}         onReset={handleReset}
      />
      <main className="main-layout">
        <CodeEditor
          code={code}               output={output}
          isError={isError}         isaMode={isaMode}
          onCodeChange={setCode}    onAssemble={handleAssemble}
          onExport={handleExport}
        />
        <ResultsPanel
          instructions={assembled}
          onExportResults={handleExportResults}
        />
        <RegisterPanel
          registers={registers}
          displayFormat={displayFormat}
          onFormatChange={setFormat}
        />
      </main>
    </div>
  )
}

export default App
