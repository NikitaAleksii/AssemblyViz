import { useState, useEffect, useRef } from 'react'
import Navbar from './components/Navbar'
import CodeEditor from './components/CodeEditor'
import MemoryPanel from './components/MemoryPanel'
import ResultsPanel from './components/ResultsPanel'
import RegisterPanel from './components/RegisterPanel'
import {
  AssembledInstruction, MemorySlot, Register,
  ISAMode, DisplayFormat,
  HYMN_REGISTERS, RISCV_DEFAULT_REGISTERS,
  buildHYMNMemory, buildRISCVMemory,
} from './types'
import './App.css'

function App() {
  const [code, setCode]             = useState('')
  const [output, setOutput]         = useState('')
  const [isError, setIsError]       = useState(false)
  const [isaMode, setISAMode]       = useState<ISAMode>('HYMN')
  const [speedMs, setSpeedMs]       = useState(200)
  const [activeTab, setActiveTab]   = useState<'editor' | 'memory'>('editor')
  const [displayFormat, setFormat]  = useState<DisplayFormat>('HEXADECIMAL')

  const [assembled, setAssembled]       = useState<AssembledInstruction[]>([])
  const [memorySlots, setMemorySlots]   = useState<MemorySlot[]>(buildHYMNMemory())
  const [registers, setRegisters]       = useState<Register[]>(HYMN_REGISTERS)
  const [currentStep, setCurrentStep]   = useState(-1)

  const runTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  // ── When ISA mode changes, reset memory and registers ───────
  useEffect(() => {
    setMemorySlots(isaMode === 'HYMN' ? buildHYMNMemory() : buildRISCVMemory(0))
    setRegisters(isaMode === 'HYMN' ? [...HYMN_REGISTERS] : [...RISCV_DEFAULT_REGISTERS])
    setAssembled([])
    setCurrentStep(-1)
    showOutput(`${isaMode} mode selected.`)
  }, [isaMode])

  function showOutput(msg: string, error = false) {
    setOutput(msg); setIsError(error)
  }

  function stopRun() {
    if (runTimer.current) { clearInterval(runTimer.current); runTimer.current = null }
  }

  function getCleanLines(src: string) {
    return src.split('\n')
      .map((raw, i) => ({ raw, trimmed: raw.trim(), idx: i }))
      .filter(l => l.trimmed !== '')
  }

  function buildRegisters(step: number, lines: AssembledInstruction[]): Register[] {
    if (step < 0 || step >= lines.length) {
      return isaMode === 'HYMN' ? [...HYMN_REGISTERS] : [...RISCV_DEFAULT_REGISTERS]
    }
    const instr = lines[step].instruction
    if (isaMode === 'HYMN') {
      return [
        { name: 'PC', number: 0, value: step },
        { name: 'IR', number: 1, value: instr.slice(0, 8).toUpperCase() },
        { name: 'AC', number: 2, value: (step + 1) * 8 },
      ]
    }
    // RISC-V: update just PC, others stay 0 until backend wires up
    return RISCV_DEFAULT_REGISTERS.map((r, i) =>
      i === 0 ? { ...r, value: step } : r
    )
  }

  // ── Assemble ─────────────────────────────────────────────────
  function handleAssemble(): boolean {
    stopRun()
    if (!code.trim()) {
      setAssembled([])
      setCurrentStep(-1)
      showOutput('Cannot assemble empty code.', true)
      return false
    }
    const lines = getCleanLines(code)
    if (!lines.length) { showOutput('No valid lines found.', true); return false }

    // TODO: replace with real backend call
    const newAssembled: AssembledInstruction[] = lines.map((l, i) => ({
      address: isaMode === 'HYMN'
        ? i.toString(2).padStart(5, '0')
        : `0x${(i * 4).toString(16).padStart(8, '0')}`,
      code: isaMode === 'HYMN'
        ? `${i.toString(2).padStart(4, '0')} 0000`
        : `${i.toString(2).padStart(4, '0')} ${(i+1).toString(2).padStart(4, '0')}`,
      instruction: l.trimmed,
      isActive: false,
    }))

    // Update memory slots to match assembled instructions
    if (isaMode === 'HYMN') {
      const slots = buildHYMNMemory()
      newAssembled.forEach((instr, i) => { if (i < slots.length) slots[i].instruction = instr.instruction })
      setMemorySlots(slots)
    } else {
      setMemorySlots(buildRISCVMemory(newAssembled.length).map((slot, i) => ({
        ...slot, instruction: newAssembled[i].instruction
      })))
    }

    setAssembled(newAssembled)
    setCurrentStep(-1)
    setRegisters(buildRegisters(-1, newAssembled))
    showOutput(`Assembled ${newAssembled.length} line(s) in ${isaMode} mode.`)
    return true
  }

  // ── Step Forward ─────────────────────────────────────────────
  function handleStep() {
    if (!assembled.length) { handleAssemble(); return }
    if (currentStep >= assembled.length - 1) { stopRun(); showOutput('End of program.'); return }

    const next    = currentStep + 1
    const updated = assembled.map((l, i) => ({ ...l, isActive: i === next }))
    const updatedMem = memorySlots.map((s, i) => ({ ...s, isActive: i === next }))

    setAssembled(updated)
    setMemorySlots(updatedMem)
    setCurrentStep(next)
    setRegisters(buildRegisters(next, updated))
    showOutput(`Step ${next + 1}: ${updated[next].instruction}`)
  }

  // ── Step Back ────────────────────────────────────────────────
  function handleBack() {
    stopRun()
    if (!assembled.length) { showOutput('Nothing to go back through.', true); return }

    const next    = Math.max(currentStep - 1, -1)
    const updated = assembled.map((l, i) => ({ ...l, isActive: i === next }))
    const updatedMem = memorySlots.map((s, i) => ({ ...s, isActive: i === next }))

    setAssembled(updated)
    setMemorySlots(updatedMem)
    setCurrentStep(next)
    setRegisters(buildRegisters(next, updated))
    if (next < 0) showOutput('Returned to start.')
    else showOutput(`Moved back to step ${next + 1}: ${updated[next].instruction}`)
  }

  // ── Play ─────────────────────────────────────────────────────
  function handlePlay() {
    if (!assembled.length) { handleAssemble(); return }
    stopRun()
    showOutput('Running...')
    runTimer.current = setInterval(() => {
      setCurrentStep(prev => {
        const next = prev + 1
        setAssembled(lines => {
          if (next >= lines.length) { stopRun(); showOutput('Run complete.'); return lines }
          const updated = lines.map((l, i) => ({ ...l, isActive: i === next }))
          setMemorySlots(mem => mem.map((s, i) => ({ ...s, isActive: i === next })))
          setRegisters(buildRegisters(next, updated))
          showOutput(`Step ${next + 1}: ${updated[next].instruction}`)
          return updated
        })
        return next
      })
    }, speedMs)
  }

  // ── Reset ────────────────────────────────────────────────────
  function handleReset() {
    stopRun()
    setCode('')
    setAssembled([])
    setCurrentStep(-1)
    setMemorySlots(isaMode === 'HYMN' ? buildHYMNMemory() : buildRISCVMemory(0))
    setRegisters(isaMode === 'HYMN' ? [...HYMN_REGISTERS] : [...RISCV_DEFAULT_REGISTERS])
    showOutput('Reset.')
  }

  function handleExport() {
    if (!code.trim()) { showOutput('Nothing to export.', true); return }
    const blob = new Blob([code], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'assembly-code.txt'; a.click()
    URL.revokeObjectURL(url)
    showOutput('Exported.')
  }

  function handleExportResults() {
    if (!assembled.length) { showOutput('No results to export.', true); return }
    const text = assembled.map(l => `${l.address}    ${l.code}    ${l.instruction}`).join('\n')
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'results.txt'; a.click()
    URL.revokeObjectURL(url)
    showOutput('Results exported.')
  }

  useEffect(() => () => stopRun(), [])

  return (
    <div className="app-shell">
      <Navbar
        activeTab={activeTab}     onTabChange={setActiveTab}
        isaMode={isaMode}         onISAChange={setISAMode}
        speedMs={speedMs}         onSpeedChange={setSpeedMs}
        onBack={handleBack}       onPlay={handlePlay}
        onStep={handleStep}       onReset={handleReset}
      />
      <main className="main-layout">
        {/* Left panel switches between Code Editor and Memory */}
        {activeTab === 'editor'
          ? <CodeEditor
              code={code}             output={output}
              isError={isError}       isaMode={isaMode}
              onCodeChange={setCode}  onAssemble={handleAssemble}
              onExport={handleExport}
            />
          : <MemoryPanel
              slots={memorySlots}
              displayFormat={displayFormat}
              onFormatChange={setFormat}
            />
        }

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
