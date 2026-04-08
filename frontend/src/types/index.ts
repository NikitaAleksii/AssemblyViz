/** One assembled instruction shown in the Results panel */
export interface AssembledInstruction {
  address: string
  code: string
  instruction: string
  isActive: boolean
}

/** One memory slot shown in the Memory panel */
export interface MemorySlot {
  address: string       // binary (HYMN) or hex (RISC-V)
  instruction: string   // decoded mnemonic text
  value?: number        // raw numeric word (used for HEX / DECIMAL display)
  isActive: boolean
  isChanged?: boolean   // flashes true for one step when the cell value changed
}

/** One CPU register */
export interface Register {
  name: string
  number: number
  value: number | string
}

export type ISAMode = 'HYMN' | 'RISC-V'
export type DisplayFormat = 'HEXADECIMAL' | 'DECIMAL' | 'INSTRUCTION'

// ── HYMN: 3 registers ────────────────────────────────────────
export const HYMN_REGISTERS: Register[] = [
  { name: 'PC', number: 0, value: 0 },
  { name: 'IR', number: 1, value: 0 },
  { name: 'AC', number: 2, value: 0 },
]

// ── RISC-V: 32 registers ─────────────────────────────────────
export const RISCV_REGISTER_NAMES = [
  'ZERO','RA','SP','GP','TP',
  'T0','T1','T2',
  'S0','S1',
  'A0','A1','A2','A3','A4','A5','A6','A7',
  'S2','S3','S4','S5','S6','S7','S8','S9','S10','S11',
  'T3','T4','T5','T6',
]

export const RISCV_DEFAULT_REGISTERS: Register[] = RISCV_REGISTER_NAMES.map(
  (name, i) => ({ name, number: i, value: 0 })
)

// ── HYMN: 30 memory slots (5-bit binary addresses 00000–11101) ─
export function buildHYMNMemory(): MemorySlot[] {
  return Array.from({ length: 30 }, (_, i) => ({
    address: i.toString(2).padStart(5, '0'),
    instruction: 'HALT',
    isActive: false,
  }))
}

// ── RISC-V: variable memory — one slot per instruction ───────
export function buildRISCVMemory(count: number): MemorySlot[] {
  return Array.from({ length: count }, (_, i) => ({
    address: `0x${(i * 4).toString(16).padStart(8, '0')}`,
    instruction: 'HALT',
    isActive: false,
  }))
}
