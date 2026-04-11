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
    <section className="left-panel">
      <div className="panel-header">
        <h2>CODE EDITOR</h2>
        <div className="editor-actions">
          {/*
           * Hidden file input — clicking it directly via a ref lets the visible
           * IMPORT button trigger the OS file picker without exposing the default
           * file-input styling.
           */}
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
      <div className="editor-box">
        {/* Line-number gutter — scroll position is driven by syncScroll, not the user */}
        <div ref={lineNumbersRef} className="line-numbers">
          {lineNumbers.map(n => <span key={n}>{n}</span>)}
        </div>
        <textarea
          value={code}
          onChange={e => onCodeChange(e.target.value)}
          onScroll={syncScroll}
          placeholder={`Write ${isaMode} code here...`}
          spellCheck={false}
        />
      </div>

      {/* Output section: IO console on top, assembler/step status line below */}
      <div className="output-section">
        <h3>OUTPUT</h3>
        <div className="output-box">
          {/* Show a placeholder when the program has produced no console output yet */}
          {consoleOutput || <span className="output-placeholder">No output yet...</span>}
        </div>
        {/* Status line only renders when there is a message to show */}
        {output && (
          <div className="status-line" style={{ color: isError ? '#c62828' : '#888' }}>
            {output}
          </div>
        )}
      </div>
    </section>
  )
}

export default CodeEditor
