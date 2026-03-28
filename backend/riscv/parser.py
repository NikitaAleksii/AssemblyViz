import re
from dataclasses import dataclass, field

# @dataclass is used to generate boilerplate methods for a class that's just meant to hold data
# @property lets me access methods as if there were attributes -- this hides internal implementation

MNEMONICS = {
    "add", "sub", "sll", "slt", "sltu", "xor", "srl", "sra", "or", "and",
    "addi", "slti", "sltiu", "xori", "ori", "andi", "slli", "srli", "srai",
    "lw", "lh", "lb", "lhu", "lbu",
    "sw", "sh", "sb",
    "beq", "bne", "blt", "bge", "bltu", "bgeu",
    "lui", "auipc",
    "jal", "jalr",
    "ecall", "ebreak",
    "li", "la", "mv", "j", "ret", "nop"   # pseudo-ops
}

REGISTER_NAMES = {
    # numeric names
    "x0",  "x1",  "x2",  "x3",  "x4",  "x5",  "x6",  "x7",
    "x8",  "x9",  "x10", "x11", "x12", "x13", "x14", "x15",
    "x16", "x17", "x18", "x19", "x20", "x21", "x22", "x23",
    "x24", "x25", "x26", "x27", "x28", "x29", "x30", "x31",
    # ABI names
    "zero",                         # x0  - hardwired zero
    "ra",                           # x1  - return address
    "sp",                           # x2  - stack pointer
    "gp",                           # x3  - global pointer
    "tp",                           # x4  - thread pointer
    "t0", "t1", "t2",               # x5-x7  - temporaries
    "s0", "s1",                     # x8-x9  - saved registers
    "a0", "a1", "a2", "a3",         # x10-x13 - function arguments
    "a4", "a5", "a6", "a7",         # x14-x17 - function arguments
    "s2", "s3", "s4",  "s5",        # x18-x21 - saved registers
    "s6", "s7", "s8",  "s9",        # x22-x25 - saved registers
    "s10", "s11",                   # x26-x27 - saved registers
    "t3", "t4", "t5", "t6",         # x28-x31 - temporaries
    # fp is an alias for s0
    "fp",                           # x8  - frame pointer
}

DIRECTIVES = {".text", ".data", ".word", ".asciz", ".string", ".ascii"}

# Reserved labels that cannot be used when user wants to create their own label
RESERVED = MNEMONICS | REGISTER_NAMES | DIRECTIVES

# Regex patterns
_LABEL_DEF = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*:$')

_ESCAPES = {"n": 10, "t": 9, "r": 13, "0": 0, "\\": 92, '"': 34, "'": 39}

# This class stores a parsed line, including line number, label (if any), mnemonic (if any), and operands
@dataclass
class ParsedLine:
    line_number: int
    label: str | None
    mnemonic: str | None
    operands: list[str]

# This class stores an error, including line number, instruction, and a message
@dataclass
class ParseError:
    line_number: int
    line_text: str
    message: str


class Parser:
    def __init__(self):
        self._parsed_lines: list[ParsedLine] = []
        self._symbol_table: dict[str, int] = {}
        self._errors: list[ParseError] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, source: str) -> list[ParsedLine] | None:
        # Reset states before each pass
        self._parsed_lines = []
        self._symbol_table = {}
        self._errors = []

        lines = source.splitlines()
        self._first_pass(lines)  # build symbol table
        self._second_pass(lines)  # build parsed lines

        if self._errors:
            return None
        return self._parsed_lines

    @property
    def symbol_table(self) -> dict[str, int]:
        return self._symbol_table

    @property
    def errors(self) -> list[ParseError]:
        return self._errors

    # ------------------------------------------------------------------
    # Passes
    # ------------------------------------------------------------------

    # Collects all labels in the symbol table. If errors are found, add them to the error list.
    def _first_pass(self, lines) -> None:
        # Split lines into text and data buckets
        text_lines = []
        data_lines = []
        current = "text"

        for line in lines:
            tokens = self._tokenize_line(line)
            if not tokens:
                continue
            if tokens[0].lower() == ".data":
                current = "data"
                continue
            if tokens[0].lower() == ".text":
                current = "text"
                continue
            if current == "text":
                text_lines.append(line)
            else:
                data_lines.append(line)

        text_pc = 0
        for index, line in enumerate(text_lines):
            tokens = self._tokenize_line(line)
            if not tokens:
                continue
            if _LABEL_DEF.fullmatch(tokens[0]):
                label_name = tokens[0][:-1]

                if self._register_label(label_name, text_pc, index+1, ' '.join(tokens)):
                    if len(tokens) > 1:
                        text_pc += self._pseudo_size(tokens[1:]) * 4
            else:
                text_pc += self._pseudo_size(tokens) * 4

        # Scan data line right after the text section
        data_pc = text_pc
        for index, line in enumerate(data_lines):
            tokens = self._tokenize_line(line)
            if not tokens:
                continue
            if _LABEL_DEF.fullmatch(tokens[0]):
                label_name = tokens[0][:-1]

                if self._register_label(label_name, data_pc, index+1, ' '.join(tokens)):
                    if len(tokens) > 1:
                        data_pc += self._data_size(tokens[1:])
            else:
                data_pc += self._data_size(tokens)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _register_label(self, label_name: str, address: int, line_number: int, line_text: str) -> bool:
        if label_name.lower() in RESERVED:
            self._add_error(line_number, line_text, f"'{label_name}' is a reserved word and cannot be used as a label")
            return False
        if label_name in self._symbol_table:
            self._add_error(line_number, line_text, f"Duplicate label: '{label_name}'")
            return False
        self._symbol_table[label_name] = address
        return True

    # Tokenizes a line
    def _tokenize_line(self, line: str) -> list[str]:
        tokenized_line = line.split("#")[0].strip()  # do not include comments
        if not tokenized_line:
            return []
        return tokenized_line.replace(",", "").split()

    # Adds an error of ParseError class
    def _add_error(self, line_number: int, line_text: str, message: str) -> None:
        self._errors.append(ParseError(line_number, line_text, message))

    # Predicts how many 32-bit words a line will emit without actually assembling it
    # This is needed during the label-scanning pass so that label addresses
    # can be calculated correctly before any encoding happens
    #
    # la always expands to 2 words
    # li expands to 1 or 2 depending on whether the immediate fits in 12 bits
    # everything else is 1
    def _pseudo_size(self, tokens: list[str]) -> int:
        if not tokens:
            return 0
        instr_temp = tokens[0].lower()
        if instr_temp == "la":
            return 2
        if instr_temp == "li":
            try:
                imm = int(tokens[2], 0)
                return 1 if -2048 <= imm <= 2047 else 2
            except (IndexError, ValueError):
                return 1
        return 1

    #  _data_size(line) returns the byte size of what _data_words would emit
    # used during the first pass to calculate data-label addresses.
    def _data_size(self, line: list[str]) -> int:
        return len(self._data_words(line)) * 4

    # Handles a single .data directive line and returns the list of 32-bit words it produces
    #
    # It dispatches on the directive type: .word parses comma-separated integers,
    # while .asciz/.string call _parse_string, append a null terminator, pad to a 4-byte boundary,
    # then call _pack_bytes_to_words. .ascii is the same but skips the null terminator.
    #
    # _data_words(".word 1, 2, 3")
    # returns [1, 2, 3]
    #
    # _data_words('.asciz "hi\n"')
    # calls _parse_string -> [104, 105, 10]
    # appends null terminator -> [104, 105, 10, 0]
    # already 4 bytes so no padding needed
    # calls _pack_bytes_to_words ->[673897576]
    # returns [673897576]
    def _data_words(self, parts: list[str]) -> list[int]:
        directive = parts[0].lower()
        args = ' '.join(parts[1:]) if len(parts) > 1 else ""

        if directive == ".word":
            return [int(v.strip(), 0) & 0xFFFFFFFF for v in args.split() if v.strip()]

        if directive in (".asciz", ".string", ".ascii"):
            byte_vals = self._parse_string(args)
            if directive != ".ascii":
                byte_vals.append(0)
            while len(byte_vals) % 4:
                byte_vals.append(0)
            return self._pack_bytes_to_words(byte_vals)

        return []

    # Converts a quoted string literal (like "hello\n") into a list of byte values
    # Handles standard escape sequences via the _ESCAPES lookup table.
    #
    # _parse_string('"hi\n"')
    # 'h' -> 104, 'i' -> 105, '\n' -> 10
    # returns [104, 105, 10]
    def _parse_string(self, raw: str) -> list[int]:
        s = raw.strip()
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]
        chars = []
        i = 0
        while i < len(s):
            if s[i] == "\\" and i + 1 < len(s):
                chars.append(_ESCAPES.get(s[i+1], ord(s[i+1])))
                i += 2
            else:
                chars.append(ord(s[i]))
                i += 1
        return chars

    # Takes a list of bytes and packs every four of them into one little-endian (LSB at the lowest memory address) 32-bit word
    # which is how strings get stored in the data section
    #
    # _pack_bytes_to_words([104, 105, 10, 0])
    # packs little-endian: byte0 | byte1<<8 | byte2<<16 | byte3<<24
    # 104 | (105 << 8) | (10 << 16) | (0 << 24)
    # returns [673897576]
    def _pack_bytes_to_words(self, byte_vals: list[int]) -> list[int]:
        words = []
        for i in range(0, len(byte_vals), 4):
            words.append(
                byte_vals[i]
                | (byte_vals[i + 1] << 8)
                | (byte_vals[i + 2] << 16)
                | (byte_vals[i + 3] << 24)
            )
        return words