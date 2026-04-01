/** One assembled instruction shown in the Results panel */
export interface AssembledInstruction {
  address: string;      // e.g. "0x0000"
  code: string;         // e.g. "H000"
  instruction: string;  // e.g. "LOAD 23"
  isActive: boolean;    // true = currently highlighted row
}

/** One CPU register */
export interface Register {
  name: string;         // "PC", "IR", "AC"
  number: number;       // 0, 1, 2 ...
  value: number | string; // numeric value or string like "HALT"
}

export type ISAMode = 'HYMN' | 'RISC-V';
export type DisplayFormat = 'HEXADECIMAL' | 'DECIMAL' | 'BINARY';
