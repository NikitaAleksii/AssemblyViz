/**
 * App.tsx
 *
 * Root component for AssemblyViz — an interactive assembly simulator supporting
 * two ISA modes: HYMN (a simple educational ISA) and RISC-V.
 *
 * Responsibilities:
 *  - Owns all top-level simulation state (registers, memory, assembled instructions)
 *  - Drives the assemble → step → play → back → reset lifecycle via backend API calls
 *  - Passes derived state and handlers down to Navbar, CodeEditor, MemoryPanel,
 *    ResultsPanel, and RegisterPanel
 */

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

/**
 * A snapshot of simulator state at a single point in execution history.
 * Pushed onto `stepHistory` before every forward step so the user can step back.
 */
interface HistoryEntry {
  registers: Register[]
  memorySlots: MemorySlot[]
  /** The index of the instruction that was active when this snapshot was taken (-1 = before first step). */
  currentStep: number
  inputQueuePos: number
}

/**
 * All inputs needed to execute one simulation step.
 * Passed explicitly so `performStep` is a pure-ish function that does not
 * capture stale React state from closures.
 */
interface StepParams {
  /** Raw machine-word array produced by the assembler (HYMN only). */
  words: number[]
  registers: Register[]
  memorySlots: MemorySlot[]
  assembled: AssembledInstruction[]
  /** Index of the last executed instruction (-1 before the first step). */
  currentStep: number
  mode: ISAMode
  /** Original source text, required for RISC-V's replay-from-scratch strategy. */
  source: string
  inputQueue: string[]
  inputQueuePos: number
}

/**
 * The subset of state returned by `performStep` that the play-loop needs
 * to thread through successive steps without relying on React state updates
 * (which are asynchronous and would otherwise be stale inside a timer callback).
 */
interface StepResult {
  registers: Register[]
  memorySlots: MemorySlot[]
  currentStep: number
  /** False when the program has halted or run past the last instruction. */
  shouldContinue: boolean
  inputQueuePos: number
}

function App() {
  // ── Editor / UI state ─────────────────────────────────────────
  const [code, setCode]             = useState('')
  const [output, setOutput]         = useState('')
  const [isError, setIsError]       = useState(false)
  const [consoleOutput, setConsole] = useState('')
  const [isaMode, setISAMode]       = useState<ISAMode>('HYMN')
  const [speedMs, setSpeedMs]       = useState(200)
  const [activeTab, setActiveTab]    = useState<'editor' | 'memory'>('editor')
  const [memoryFormat, setMemFmt]   = useState<DisplayFormat>('HEXADECIMAL')
  const [registerFormat, setRegFmt] = useState<DisplayFormat>('HEXADECIMAL')

  // ── Simulation state ──────────────────────────────────────────
  const [words, setWords]             = useState<number[]>([])
  const [assembled, setAssembled]     = useState<AssembledInstruction[]>([])
  const [memorySlots, setMemorySlots] = useState<MemorySlot[]>(buildHYMNMemory())
  const [registers, setRegisters]     = useState<Register[]>(HYMN_REGISTERS)
  /** Index of the most recently executed instruction (-1 = not started). */
  const [currentStep, setCurrentStep] = useState(-1)

  // ── Refs (values that must not trigger re-renders) ────────────
  /** Handle for the currently scheduled play-loop timeout. */
  const runTimer    = useRef<ReturnType<typeof setTimeout> | null>(null)
  /** Whether the play-loop is active. Using a ref avoids stale closure issues inside setTimeout callbacks. */
  const isPlaying   = useRef(false)
  /** Stack of state snapshots enabling the "Step Back" feature. */
  const stepHistory = useRef<HistoryEntry[]>([])
  /** Mirror of `speedMs` state kept in a ref so the play-loop always reads the latest value. */
  const speedMsRef  = useRef(speedMs)
  useEffect(() => { speedMsRef.current = speedMs }, [speedMs])

  const [inputQueue, setInputQueue] = useState<string[]>([])
  const inputQueuePos = useRef<number>(0)

  // ── ISA mode change: reset everything ────────────────────────
  /**
   * When the user switches ISAs, tear down any in-progress run and reinitialise
   * all simulation state to the defaults for the newly selected architecture.
   */
  useEffect(() => {
    stopRun()
    setWords([])
    setAssembled([])
    setCurrentStep(-1)
    setMemorySlots(isaMode === 'HYMN' ? buildHYMNMemory() : buildRISCVMemory(0))
    setRegisters(isaMode === 'HYMN' ? [...HYMN_REGISTERS] : [...RISCV_DEFAULT_REGISTERS])
    stepHistory.current = []
    inputQueuePos.current = 0
    setInputQueue([])
    setConsole('')
    showOutput(`${isaMode} mode selected.`)
  }, [isaMode])

  /**
   * Display a status or error message in the output bar below the editor.
   * @param msg   - The message text to display.
   * @param error - When true, the message is styled as an error.
   */
  function showOutput(msg: string, error = false) {
    setOutput(msg); setIsError(error)
  }

  /** Cancel the play-loop timer and mark the simulator as stopped. */
  function stopRun() {
    isPlaying.current = false
    if (runTimer.current) { clearTimeout(runTimer.current); runTimer.current = null }
  }

  // ── Assemble ─────────────────────────────────────────────────
  /**
   * Send the current source code to the backend assembler for the active ISA.
   * On success, populates `assembled`, `memorySlots`, `registers`, and `words`
   * with the response data and resets step history.
   *
   * @returns `true` on success, `false` if assembly failed or the editor is empty.
   */
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
        // RISC-V: memory panel mirrors the instruction list; registers come from the backend
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
      inputQueuePos.current = 0
      setConsole('')
      showOutput(`Assembled ${data.instructions.length} line(s) in ${isaMode} mode.`)
      return true
    } catch {
      showOutput('Network error: could not reach backend.', true)
      return false
    }
  }

  // ── Core step: takes explicit params, returns new state ──────
  /**
   * Execute one instruction step by calling the backend step API.
   *
   * Before making the API call, the current state is pushed onto `stepHistory`
   * so it can be restored by `handleBack`. If the step fails the snapshot is
   * popped to keep the history consistent.
   *
   * Strategy differs by ISA:
   *  - **HYMN**: stateful — the backend advances a persistent machine state by one instruction.
   *  - **RISC-V**: stateless replay — the backend re-simulates from the beginning up to
   *    `step_count` instructions, so the frontend must track the execution count.
   *
   * @param p - Explicit snapshot of all simulation state at call time.
   * @returns Updated state slice and a `shouldContinue` flag, or `null` on failure / end of program.
   */
  async function performStep(p: StepParams): Promise<StepResult | null> {
    if (!p.assembled.length) return null

    // Save state for Back before modifying anything
    stepHistory.current.push({
      registers:     p.registers,
      memorySlots:   p.memorySlots,
      currentStep:   p.currentStep,
      inputQueuePos: p.inputQueuePos,
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

        const currentWord = p.memorySlots[pc]?.value ?? 0
        const isRead = ((currentWord >> 5) & 0b111) === 0b100 && (currentWord & 0b11111) === 30
        let ioInput = 0
        let nextQueuePos = p.inputQueuePos
        if (isRead) {
          const parsed = parseInt(p.inputQueue[p.inputQueuePos] ?? '', 10)
          ioInput = Number.isNaN(parsed) ? 0 : parsed
          nextQueuePos = p.inputQueuePos + 1
        }

        const res = await fetch('/api/hymn/step', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ memory: p.memorySlots.map(s => s.value ?? 0), pc, ac, io_input: ioInput }),
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
            // Highlight cells whose value changed during this step
            isChanged: s.value !== (p.memorySlots[i]?.value ?? 0),
          })
        )
        const newAssembled = p.assembled.map((l, i) => ({ ...l, isActive: i === executedIdx }))

        setAssembled(newAssembled)
        setMemorySlots(newMemSlots)
        setRegisters(newRegisters)
        setCurrentStep(executedIdx)
        if (isRead) inputQueuePos.current = nextQueuePos

        const cont = !data.halted && data.pc < p.assembled.length
        if (data.io_output?.length) {
          setConsole(prev => (prev ? prev + '  ' : '') + data.io_output.join('  '))
        }
        if (data.halted) {
          showOutput(`Halted at step ${executedIdx + 1}.`)
        } else {
          showOutput(`Step ${executedIdx + 1}: ${p.assembled[executedIdx].instruction}`)
        }
        return { registers: newRegisters, memorySlots: newMemSlots, currentStep: executedIdx, shouldContinue: cont, inputQueuePos: nextQueuePos }

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

        // Match the executed PC back to a row in the assembled listing for highlighting
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
        return { registers: newRegisters, memorySlots: newMemSlots, currentStep: execCount, shouldContinue: !data.halted, inputQueuePos: p.inputQueuePos }
      }
    } catch {
      showOutput('Network error during step.', true)
      stepHistory.current.pop()
      return null
    }
  }

  // ── Step Forward ─────────────────────────────────────────────
  /**
   * Advance the simulation by one instruction.
   * Assembles first if no instructions are loaded yet.
   */
  async function handleStep() {
    stopRun()
    if (!assembled.length) { await handleAssemble(); return }
    await performStep({ words, registers, memorySlots, assembled, currentStep, mode: isaMode, source: code, inputQueue, inputQueuePos: inputQueuePos.current })
  }

  // ── Step Back ────────────────────────────────────────────────
  /**
   * Restore the most recently saved history snapshot, effectively rewinding
   * the simulation by one instruction.
   */
  function handleBack() {
    stopRun()
    if (!stepHistory.current.length) { showOutput('Nothing to go back through.', true); return }
    const prev = stepHistory.current.pop()!
    setRegisters(prev.registers)
    setMemorySlots(prev.memorySlots)
    setCurrentStep(prev.currentStep)
    inputQueuePos.current = prev.inputQueuePos
    setAssembled(assembled.map((l, i) => ({ ...l, isActive: i === prev.currentStep })))
    if (prev.currentStep < 0) showOutput('Returned to start.')
    else showOutput(`Moved back to step ${prev.currentStep + 1}.`)
  }

  // ── Play ─────────────────────────────────────────────────────
  /**
   * Run the simulation continuously at the user-configured speed until the
   * program halts or the user stops playback.
   *
   * If no code has been assembled yet, assembles first and prompts the user
   * to press Play again so they can review the listing before execution starts.
   *
   * The play-loop uses a recursive `setTimeout` pattern (rather than `setInterval`)
   * so that each step fully completes — including its async API round-trip — before
   * the next one is scheduled. State is threaded through the loop explicitly to
   * avoid React's asynchronous state update batching.
   */
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

    let state: StepParams = { words, registers, memorySlots, assembled, currentStep, mode: isaMode, source: code, inputQueue, inputQueuePos: inputQueuePos.current }

    const loop = async () => {
      if (!isPlaying.current) return
      const result = await performStep(state)
      if (!result || !result.shouldContinue || !isPlaying.current) {
        isPlaying.current = false
        runTimer.current = null
        return
      }
      // Thread the latest state forward so the next iteration doesn't use stale React state
      state = { ...state, registers: result.registers, memorySlots: result.memorySlots, currentStep: result.currentStep, inputQueuePos: result.inputQueuePos }
      runTimer.current = setTimeout(loop, speedMsRef.current)
    }

    loop()
  }

  // ── Reset ─────────────────────────────────────────────────────
  /**
   * Stop any in-progress run and restore all simulation state to the
   * defaults for the currently selected ISA, without clearing the editor.
   */
  function handleReset() {
    stopRun()
    setWords([])
    setAssembled([])
    setCurrentStep(-1)
    setMemorySlots(isaMode === 'HYMN' ? buildHYMNMemory() : buildRISCVMemory(0))
    setRegisters(isaMode === 'HYMN' ? [...HYMN_REGISTERS] : [...RISCV_DEFAULT_REGISTERS])
    stepHistory.current = []
    inputQueuePos.current = 0
    setConsole('')
    showOutput('Reset.')
  }

  /**
   * Export the current editor contents as a plain-text `.txt` file download.
   * No-ops with an error message if the editor is empty.
   */
  function handleExport() {
    if (!code.trim()) { showOutput('Nothing to export.', true); return }
    const blob = new Blob([code], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'assembly-code.txt'; a.click()
    URL.revokeObjectURL(url)
    showOutput('Exported.')
  }

  /**
   * Export the assembled instruction listing (address, machine code, mnemonic)
   * as a plain-text `.txt` file download.
   * No-ops with an error message if nothing has been assembled yet.
   */
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

  // Stop any running timer when the component unmounts
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
              inputQueue={inputQueue}
              onInputQueueChange={setInputQueue}
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
