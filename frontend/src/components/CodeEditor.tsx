/**
 * CodeEditor.tsx
 *
 * Left-panel component that provides the assembly source editor, file import/export
 * controls, and the output/status area below the editor.
 *
 * Layout (top →-> bottom):
 *  - Panel header with IMPORT, EXPORT, and ASSEMBLE action buttons
 *  - Editor box: synchronized line-number gutter + textarea
 *  - Output section: IO console output + assembler/step status line
 */

import React, { useRef } from 'react'

/**
 * Props for the CodeEditor component.
 *
 * All state is lifted to the parent (`App`); this component is fully controlled
 * and communicates changes upward via callbacks.
 */
interface CodeEditorProps {
  code: string
  output: string
  isError: boolean
  consoleOutput: string
  isaMode: string
  /** Called whenever the user edits the source text. */
  onCodeChange: (code: string) => void
  /** Triggers assembly of the current source. May be async (returns a success flag). */
  onAssemble: () => void | Promise<boolean>
  /** Triggers download of the current source as a text file. */
  onExport: () => void
  /** Input queue lines consumed by the HYMN READ pseudo-op (one integer per entry). */
  inputQueue: string[]
  /** Called when the user edits the input textarea. */
  onInputQueueChange: (lines: string[]) => void
}

/**
 * Controlled assembly source editor with a synchronized line-number gutter,
 * file import/export, and a combined output/status display.
 *
 * `React.FC<CodeEditorProps>` is the built-in TypeScript type for a functional
 * React component that accepts the given props shape.
 */
const CodeEditor: React.FC<CodeEditorProps> = ({
  code, output, isError, consoleOutput, isaMode,
  onCodeChange, onAssemble, onExport,
  inputQueue, onInputQueueChange,
}) => {
  /** Ref to the hidden `<input type="file">` element, triggered programmatically by the IMPORT button. */
  const fileInputRef    = useRef<HTMLInputElement>(null)
  /** Ref to the line-number gutter `<div>`, kept in sync with the textarea's scroll position. */
  const lineNumbersRef  = useRef<HTMLDivElement>(null)

  /**
   * Keep the line-number gutter scrolled in lockstep with the textarea.
   * Called on every scroll event from the textarea.
   */
  const syncScroll = (e: React.UIEvent<HTMLTextAreaElement>) => {
    if (lineNumbersRef.current)
      lineNumbersRef.current.scrollTop = e.currentTarget.scrollTop
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) =>
    onInputQueueChange(e.target.value.split('\n'))
  const inputQueueText = inputQueue.join('\n')

  // Derive one number label per line from the current source text
  const lineCount = code.split('\n').length
  const lineNumbers = Array.from({ length: lineCount }, (_, i) => i + 1)

  /**
   * Handle a file selected via the hidden file input.
   * Reads the file as plain text and passes its content to `onCodeChange`.
   * Resets the input's value afterward so the same file can be re-imported.
   */
  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = ev => onCodeChange(ev.target?.result as string)
    reader.readAsText(file)
    e.target.value = '' // allow re-importing the same file without a change event being suppressed
  }

  return (
    <section className="left-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <div className="panel-header">
          <h2>CODE EDITOR</h2>
          <div className="editor-actions">
            {/* Hidden file input — clicking it directly via a ref lets the visible IMPORT button trigger the OS file picker without exposing the default file-input styling. */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".asm,.txt,.s,.hymn"
              style={{ display: 'none' }}
              onChange={handleImport}
            />
            <button onClick={() => fileInputRef.current?.click()}>IMPORT</button>
            <button onClick={onExport}>EXPORT</button>
            <button className="primary" onClick={onAssemble}>ASSEMBLE</button>
          </div>
        </div>

        {/* Editor area: gutter + textarea side-by-side */}
        <div className="editor-box" style={{ flex: 1, minHeight: 0 }}>
          <div ref={lineNumbersRef} className="line-numbers">
            {lineNumbers.map(n => <span key={n}>{n}</span>)}
          </div>
          <textarea
            value={code}
            onChange={e => onCodeChange(e.target.value)}
            onScroll={syncScroll}
            placeholder={`Write ${isaMode} code here...`}
            spellCheck={false}
            style={{ resize: 'none' }}
          />
        </div>

        {/* Input queue: shown only for HYMN, consumed by READ pseudo-op */}
        {isaMode === 'HYMN' && (
          <div className="input-section">
            <h3>INPUT</h3>
            <textarea
              className="input-box"
              value={inputQueueText}
              onChange={handleInputChange}
              placeholder={"One integer per line...\n(consumed by READ)"}
              spellCheck={false}
            />
          </div>
        )}
      </div>

      {/* Draggable divider above output */}
      <div
        style={{
          height: '6px',
          cursor: 'ns-resize',
          background: 'transparent',
          borderTop: '2px solid #e5e5e5',
          flexShrink: 0,
        }}
        onMouseDown={(e) => {
          e.preventDefault()
          const startY = e.clientY
          const output = document.getElementById('output-section') as HTMLElement
          const startHeight = output?.offsetHeight || 120
          const onMove = (moveEvent: MouseEvent) => {
            const delta = startY - moveEvent.clientY
            const newHeight = Math.min(400, Math.max(60, startHeight + delta))
            if (output) output.style.height = `${newHeight}px`
          }
          const onUp = () => {
            window.removeEventListener('mousemove', onMove)
            window.removeEventListener('mouseup', onUp)
          }
          window.addEventListener('mousemove', onMove)
          window.addEventListener('mouseup', onUp)
        }}
      />

      {/* Output section at the bottom, vertically resizable */}
      <div
        id="output-section"
        className="output-section"
        style={{
          height: '120px',
          overflow: 'auto',
          padding: '8px 14px 10px',
          flexShrink: 0,
        }}
      >
        <h3>OUTPUT</h3>
        <div className="output-box">
          {consoleOutput || <span className="output-placeholder">No output yet...</span>}
          {output && (
            <div className="status-line" style={{ color: isError ? '#c62828' : '#888' }}>
              {output}
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

export default CodeEditor
