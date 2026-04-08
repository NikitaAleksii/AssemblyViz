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

interface HistoryEntry {
  registers: Register[]
  memorySlots: MemorySlot[]
  currentStep: number
}

interface StepParams {
  words: number[]
  registers: Register[]
  memorySlots: MemorySlot[]
  assembled: AssembledInstruction[]
  currentStep: number
  mode: ISAMode
  source: string
}

interface StepResult {
  registers: Register[]
  memorySlots: MemorySlot[]
  currentStep: number
  shouldContinue: boolean
}

function App() {
  const [code, setCode]             = useState('')
  const [output, setOutput]         = useState('')
  const [isError, setIsError]       = useState(false)
  const [consoleOutput, setConsole] = useState('')
  const [isaMode, setISAMode]       = useState<ISAMode>('HYMN')
  const [speedMs, setSpeedMs]       = useState(200)
  const [activeTab, setActiveTab]    = useState<'editor' | 'memory'>('editor')
  const [memoryFormat, setMemFmt]   = useState<DisplayFormat>('HEXADECIMAL')
  const [registerFormat, setRegFmt] = useState<DisplayFormat>('HEXADECIMAL')

  const [words, setWords]             = useState<number[]>([])
  const [assembled, setAssembled]     = useState<AssembledInstruction[]>([])
  const [memorySlots, setMemorySlots] = useState<MemorySlot[]>(buildHYMNMemory())
  const [registers, setRegisters]     = useState<Register[]>(HYMN_REGISTERS)
  const [currentStep, setCurrentStep] = useState(-1)

  const runTimer    = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isPlaying   = useRef(false)
  const stepHistory = useRef<HistoryEntry[]>([])
  const speedMsRef  = useRef(speedMs)
  useEffect(() => { speedMsRef.current = speedMs }, [speedMs])

  // ── ISA mode change: reset everything ────────────────────────
  useEffect(() => {
    stopRun()
    setWords([])
    setAssembled([])
    setCurrentStep(-1)
    setMemorySlots(isaMode === 'HYMN' ? buildHYMNMemory() : buildRISCVMemory(0))
    setRegisters(isaMode === 'HYMN' ? [...HYMN_REGISTERS] : [...RISCV_DEFAULT_REGISTERS])
    stepHistory.current = []
    setConsole('')
    showOutput(`${isaMode} mode selected.`)
  }, [isaMode])

  function showOutput(msg: string, error = false) {
    setOutput(msg); setIsError(error)
  }

  function stopRun() {
    isPlaying.current = false
    if (runTimer.current) { clearTimeout(runTimer.current); runTimer.current = null }
  }

  // ── Assemble ─────────────────────────────────────────────────
  async function handleAssemble(): Promise<boolean> {
    stopRun()
    if (!code.trim()) {
      setAssembled([]); setCurrentStep(-1)
      showOutput('Cannot assemble empty code.', true)
      return false
    }
    const endpoint = isaMode === 'HYMN' ? '/api/hymn/assemble' : '/api/riscv/assemble'
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: code }),
      })
      if (!res.ok) {
        const err = await res.json()
        const errors = err.detail?.errors
        const msg = Array.isArray(errors) && errors.length
          ? `Line ${errors[0].line}: ${errors[0].message}`
          : (typeof err.detail === 'string' ? err.detail : 'Assembly failed.')
        showOutput(msg, true)
        return false
      }
      const data = await res.json()

      setWords(data.words)
      setAssembled(data.instructions.map((i: AssembledInstruction) => ({ ...i, isActive: false })))

      if (isaMode === 'HYMN') {
        setMemorySlots(data.memory.map((s: { address: string; decoded: string; value: number }) => ({
          address: s.address, instruction: s.decoded, value: s.value, isActive: false,
        })))
        setRegisters([
          { name: 'PC', number: 0, value: data.registers.pc },
          { name: 'IR', number: 1, value: data.registers.ir },
          { name: 'AC', number: 2, value: data.registers.ac },
        ])
      } else {
        setMemorySlots(data.instructions.map((s: { address: string; code: string; instruction: string }) => ({
          address: s.address, instruction: s.instruction, value: parseInt(s.code, 16), isActive: false,
        })))
        setRegisters(data.registers.map((r: { index: number; names: string; value: number }) => ({
          name:   r.names.toUpperCase(),
          number: r.index,
          value:  r.value,
        })))
      }

      setCurrentStep(-1)
      stepHistory.current = []
      setConsole('')
      showOutput(`Assembled ${data.instructions.length} line(s) in ${isaMode} mode.`)
      return true
    } catch {
      showOutput('Network error: could not reach backend.', true)
      return false
    }
  }

  // ── Core step: takes explicit params, returns new state ──────
  async function performStep(p: StepParams): Promise<StepResult | null> {
    if (!p.assembled.length) return null

    // Save state for Back before modifying anything
    stepHistory.current.push({
      registers:   p.registers,
      memorySlots: p.memorySlots,
      currentStep: p.currentStep,
    })

    try {
      if (p.mode === 'HYMN') {
        const pc = p.registers.find(r => r.name === 'PC')?.value as number ?? 0
        const ac = p.registers.find(r => r.name === 'AC')?.value as number ?? 0

        if (pc >= p.assembled.length) {
          showOutput('End of program.')
          stepHistory.current.pop()
          return null
        }

        const res = await fetch('/api/hymn/step', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ memory: p.memorySlots.map(s => s.value ?? 0), pc, ac }),
        })
        if (!res.ok) {
          showOutput('Step failed.', true)
          stepHistory.current.pop()
          return null
        }
        const data = await res.json()

        const executedIdx = pc
        const newRegisters: Register[] = [
          { name: 'PC', number: 0, value: data.pc },
          { name: 'IR', number: 1, value: data.ir },
          { name: 'AC', number: 2, value: data.ac },
        ]
        const newMemSlots: MemorySlot[] = data.memory.map(
          (s: { address: string; decoded: string; value: number }, i: number) => ({
            address:   s.address,
            instruction: s.decoded,
            value:     s.value,
            isActive:  i === executedIdx,
            isChanged: s.value !== (p.memorySlots[i]?.value ?? 0),
          })
        )
        const newAssembled = p.assembled.map((l, i) => ({ ...l, isActive: i === executedIdx }))

        setAssembled(newAssembled)
        setMemorySlots(newMemSlots)
        setRegisters(newRegisters)
        setCurrentStep(executedIdx)

        const cont = !data.halted && data.pc < p.assembled.length
        if (data.io_output?.length) {
          setConsole(prev => (prev ? prev + '  ' : '') + data.io_output.join('  '))
        }
        if (data.halted) {
          showOutput(`Halted at step ${executedIdx + 1}.`)
        } else {
          showOutput(`Step ${executedIdx + 1}: ${p.assembled[executedIdx].instruction}`)
        }
        return { registers: newRegisters, memorySlots: newMemSlots, currentStep: executedIdx, shouldContinue: cont }

      } else {
        // RISC-V: re-simulate from scratch to execution count N
        // currentStep = actual execution count (-1 before start)
        const execCount = p.currentStep + 1   // number of steps to execute this call

        const res = await fetch('/api/riscv/step', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source: p.source, step_count: execCount }),
        })
        if (!res.ok) {
          showOutput('Step failed.', true)
          stepHistory.current.pop()
          return null
        }
        const data = await res.json()

        // Find display row matching the PC that was just executed
        const executedPcHex = `0x${data.executed_pc.toString(16).padStart(8, '0')}`
        const highlightIdx = p.assembled.findIndex(row => row.address === executedPcHex)

        const newRegisters: Register[] = data.registers.map(
          (r: { index: number; names: string; value: number }) => ({
            name: r.names.toUpperCase(), number: r.index, value: r.value,
          })
        )
        const newMemSlots  = p.memorySlots.map((s, i) => ({ ...s, isActive: i === highlightIdx }))
        const newAssembled = p.assembled.map((l, i) => ({ ...l, isActive: i === highlightIdx }))

        setAssembled(newAssembled)
        setMemorySlots(newMemSlots)
        setRegisters(newRegisters)
        setCurrentStep(execCount)
        if (data.io_output?.length) {
          setConsole(prev => (prev ? prev + data.io_output.join('') : data.io_output.join('')))
        }
        const instrName = highlightIdx >= 0 ? p.assembled[highlightIdx].instruction : ''
        showOutput(
          data.halted
            ? `Halted at step ${execCount}.`
            : `Step ${execCount}: ${instrName}`
        )
        return { registers: newRegisters, memorySlots: newMemSlots, currentStep: execCount, shouldContinue: !data.halted }
      }
    } catch {
      showOutput('Network error during step.', true)
      stepHistory.current.pop()
      return null
    }
  }

  // ── Step Forward ─────────────────────────────────────────────
  async function handleStep() {
    stopRun()
    if (!assembled.length) { await handleAssemble(); return }
    await performStep({ words, registers, memorySlots, assembled, currentStep, mode: isaMode, source: code })
  }

  // ── Step Back ────────────────────────────────────────────────
  function handleBack() {
    stopRun()
    if (!stepHistory.current.length) { showOutput('Nothing to go back through.', true); return }
    const prev = stepHistory.current.pop()!
    setRegisters(prev.registers)
    setMemorySlots(prev.memorySlots)
    setCurrentStep(prev.currentStep)
    setAssembled(assembled.map((l, i) => ({ ...l, isActive: i === prev.currentStep })))
    if (prev.currentStep < 0) showOutput('Returned to start.')
    else showOutput(`Moved back to step ${prev.currentStep + 1}.`)
  }

  // ── Play ─────────────────────────────────────────────────────
  async function handlePlay() {
    if (!assembled.length) {
      const ok = await handleAssemble()
      if (!ok) return
      showOutput('Assembled. Press Play to run.')
      return
    }
    stopRun()
    isPlaying.current = true
    showOutput('Running...')

    let state: StepParams = { words, registers, memorySlots, assembled, currentStep, mode: isaMode, source: code }

    const loop = async () => {
      if (!isPlaying.current) return
      const result = await performStep(state)
      if (!result || !result.shouldContinue || !isPlaying.current) {
        isPlaying.current = false
        runTimer.current = null
        return
      }
      state = { ...state, registers: result.registers, memorySlots: result.memorySlots, currentStep: result.currentStep }
      runTimer.current = setTimeout(loop, speedMsRef.current)
    }

    loop()
  }

  // ── Reset ─────────────────────────────────────────────────────
  function handleReset() {
    stopRun()
    setWords([])
    setAssembled([])
    setCurrentStep(-1)
    setMemorySlots(isaMode === 'HYMN' ? buildHYMNMemory() : buildRISCVMemory(0))
    setRegisters(isaMode === 'HYMN' ? [...HYMN_REGISTERS] : [...RISCV_DEFAULT_REGISTERS])
    stepHistory.current = []
    setConsole('')
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
        {activeTab === 'editor'
          ? <CodeEditor
              code={code}               output={output}
              isError={isError}         isaMode={isaMode}
              consoleOutput={consoleOutput}
              onCodeChange={setCode}    onAssemble={handleAssemble}
              onExport={handleExport}
            />
          : <MemoryPanel
              slots={memorySlots}
              displayFormat={memoryFormat}
              onFormatChange={setMemFmt}
            />
        }
        <ResultsPanel
          instructions={assembled}
          onExportResults={handleExportResults}
        />
        <RegisterPanel
          registers={registers}
          displayFormat={registerFormat}
          onFormatChange={setRegFmt}
        />
      </main>
    </div>
  )
}

export default App
