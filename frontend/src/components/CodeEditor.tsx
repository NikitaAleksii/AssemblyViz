import React, { useRef } from 'react'

interface CodeEditorProps {
  code: string
  output: string
  isError: boolean
  isaMode: string
  onCodeChange: (code: string) => void
  onAssemble: () => void
  onExport: () => void
}

const CodeEditor: React.FC<CodeEditorProps> = ({
  code, output, isError, isaMode,
  onCodeChange, onAssemble, onExport,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Dynamic line numbers based on content
  const lineCount = Math.max(code.split('\n').length, 6)
  const lineNumbers = Array.from({ length: lineCount }, (_, i) => i + 1)

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = ev => onCodeChange(ev.target?.result as string)
    reader.readAsText(file)
    e.target.value = '' // allow re-importing same file
  }

  return (
    <section className="left-panel">
      <div className="panel-header">
        <h2>CODE EDITOR</h2>
        <div className="editor-actions">
          {/* Hidden file input */}
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

      <div className="editor-box">
        <div className="line-numbers">
          {lineNumbers.map(n => <span key={n}>{n}</span>)}
        </div>
        <textarea
          value={code}
          onChange={e => onCodeChange(e.target.value)}
          placeholder={`Write ${isaMode} code here...`}
          spellCheck={false}
        />
      </div>

      <div className="output-section">
        <h3>OUTPUT</h3>
        <div
          className="output-box"
          style={{ color: isError ? '#c62828' : '#666', fontStyle: 'normal' }}
        >
          {output || 'No output yet...'}
        </div>
      </div>
    </section>
  )
}

export default CodeEditor
