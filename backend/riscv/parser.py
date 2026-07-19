"""
Two-pass RISC-V assembly parser.

Pass 1 (_first_pass) scans all lines to build a symbol table mapping label
names to byte addresses, accounting for pseudo-instruction expansion (e.g.
`la` always emits 2 words, `li` emits 1 or 2 depending on the immediate).

Pass 2 (_second_pass) walks every line again, validates each mnemonic and its
operands against the ISA type tables imported from riscv.isa, resolves label
references against the symbol table, and emits a ParsedLine for each
instruction or data directive.

Any validation failure appends a ParseError and causes parse() to return None
instead of the parsed-line list.

Supported .data directives: .word, .ascii, .asciz, .string.
String bytes are null-terminated (except .ascii), 4-byte aligned,
and little-endian 32-bit words.
"""

import re
from dataclasses import dataclass
from riscv.isa import (
    MNEMONICS_SET, REGISTER_NAMES, DIRECTIVES,
    R_TYPE, I_TYPE, LOAD_TYPE, STORE_TYPE, BRANCH_TYPE,
    U_TYPE, JAL_TYPE, JALR_TYPE, NO_OPERAND,
    LA_TYPE, LI_TYPE, MV_TYPE, J_TYPE
)

# Reserved labels that cannot be used when user wants to create their own label
RESERVED = MNEMONICS_SET | set(REGISTER_NAMES) | DIRECTIVES

# ------------------------------------------------------------------
# Regex patterns
# ------------------------------------------------------------------

_LABEL_DEF   = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*:$')
_LABEL_REF   = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_REGISTER = re.compile(r'^(x([0-9]|[12][0-9]|3[01])|zero|ra|sp|gp|tp|t[0-6]|s([0-9]|1[01])|a[0-7]|fp)$')
_IMMEDIATE   = re.compile(r'^-?0x[0-9a-fA-F]+$|^-?\d+$')
# offset(base): offset is an optional decimal/hex immediate, base is checked
# against _REGISTER separately for a targeted error message
_MEM_OPERAND = re.compile(r'^(-?(?:0x[0-9a-fA-F]+|\d+))?\((\w+)\)$')

_ESCAPES = {"n": 10, "t": 9, "r": 13, "0": 0, "\\": 92, '"': 34, "'": 39}


# Parses the integer forms _IMMEDIATE admits: decimal or 0x hex.
# Unlike int(x, 0), leading-zero decimals ('010') are read as decimal
# instead of raising, so every regex-validated token parses cleanly.
def parse_int(text: str) -> int:
    text = text.strip()
    return int(text, 16) if text.lstrip("-").startswith("0x") else int(text, 10)

# ------------------------------------------------------------------
# Data classes
# @dataclass is used to generate boilerplate methods for a class that's just meant to hold data
# ------------------------------------------------------------------

# This class stores a parsed line, including line number, label (if any), mnemonic (if any), and operands
@dataclass
class ParsedLine:
    line_number: int
    label: str | None
    mnemonic: str | None
    operands: list[str]
    data_words: list[int] | None = None

# This class stores an error, including line number, instruction, and a message
@dataclass
class ParseError:
    line_number: int
    line_text: str
    message: str


# ------------------------------------------------------------------
# Parser
# ------------------------------------------------------------------

class Parser:
    def __init__(self):
        self._parsed_lines: list[ParsedLine] = []
        self._symbol_table: dict[str, int] = {}
        self._errors: list[ParseError] = []
        self._text_lines: list[str] = []
        self._data_lines: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, source: str) -> list[ParsedLine] | None:
        # Reset states before each pass
        self._parsed_lines = []
        self._symbol_table = {}
        self._errors = []
        self._text_lines = []
        self._data_lines = []

        lines = source.splitlines()
        self._split_lines(lines)
        self._first_pass()   # build symbol table
        self._second_pass()  # build parsed lines

        if self._errors:
            return None
        return self._parsed_lines

    # @property lets me access methods as if there were attributes -- this hides internal implementation
    @property
    def symbol_table(self) -> dict[str, int]:
        return self._symbol_table

    @property
    def errors(self) -> list[ParseError]:
        return self._errors

    # ------------------------------------------------------------------
    # Passes
    # ------------------------------------------------------------------

    # Add instructions/data into separate sections
    def _split_lines(self, lines: list[str]) -> None:
        self._text_lines = []
        self._data_lines = []
        current = "text"
        for line_number, line in enumerate(lines, start=1):
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
                self._text_lines.append((line_number, line))
            else:
                self._data_lines.append((line_number, line))

    # Collects all labels in the symbol table. If errors are found, add them to the error list.
    def _first_pass(self) -> None:
        # Scan text line labels
        text_pc = 0
        for line_number, line in self._text_lines:
            tokens = self._tokenize_line(line)
            if not tokens:
                continue
            if _LABEL_DEF.fullmatch(tokens[0]):  # checks current label with regex
                label_name = tokens[0][:-1]       # removes colon
                if self._register_label(label_name, text_pc, line_number, ' '.join(tokens)):
                    if len(tokens) > 1:           # check if there is an instruction right after label
                        text_pc += self._pseudo_size(tokens[1:]) * 4
            else:
                text_pc += self._pseudo_size(tokens) * 4

        # Scan data line labels right after the text section
        data_pc = text_pc
        for line_number, line in self._data_lines:
            tokens = self._tokenize_line(line)
            if not tokens:
                continue
            if _LABEL_DEF.fullmatch(tokens[0]):  # checks current label with regex
                label_name = tokens[0][:-1]       # removes colon
                if self._register_label(label_name, data_pc, line_number, ' '.join(tokens)):
                    if len(tokens) > 1:           # check if there is data right after label
                        data_pc += self._data_size(tokens[1:])
            else:
                data_pc += self._data_size(tokens)

    # Walks each text and data line, validates mnemonics and operands, 
    # and produces a ParsedLine object for each instruction or directive
    def _second_pass(self) -> None:
        pending_label = None

        for line_number, line in self._text_lines:
            tokens = self._tokenize_line(line)
            if not tokens:
                continue

            label_name = pending_label
            pending_label = None

            if _LABEL_DEF.fullmatch(tokens[0]):  # checks current label with regex
                label_name = tokens[0][:-1]       # removes colon
                tokens = tokens[1:]
                if not tokens:
                    pending_label = label_name
                    continue                       # label only line

            mnemonic = tokens[0].lower()
            if mnemonic not in MNEMONICS_SET:
                self._add_error(line_number, ' '.join(tokens), f"Unknown mnemonic: '{mnemonic}'")
                continue

            operands = tokens[1:]

            if not self._validate_operands(mnemonic, operands, line_number, ' '.join(tokens)):
                continue

            self._parsed_lines.append(ParsedLine(
                line_number=line_number,
                label=label_name,
                mnemonic=mnemonic,
                operands=operands
            ))

        for line_number, line in self._data_lines:
            tokens = self._tokenize_line(line)
            if not tokens:
                continue

            # strip label if present
            label = None
            if _LABEL_DEF.fullmatch(tokens[0]):
                label = tokens[0][:-1]
                tokens = tokens[1:]
                if not tokens:
                    continue  # label-only line

            directive = tokens[0].lower()

            if directive not in DIRECTIVES - {".text", ".data"}:
                self._add_error(line_number, ' '.join(tokens), f"Unknown directive: '{directive}'")
                continue

            try:
                data_words = self._data_words(tokens)
            except ValueError as e:
                self._add_error(line_number, ' '.join(tokens), str(e))
                continue

            self._parsed_lines.append(ParsedLine(
                line_number=line_number,
                label=label,
                mnemonic=directive,
                operands=tokens[1:],
                data_words=data_words
            ))

    # ------------------------------------------------------------------
    # Private helpers — general
    # ------------------------------------------------------------------

    # Tokenizes a line: '#' starts a comment and commas/whitespace separate
    # tokens, but only OUTSIDE string literals — a quoted string (quotes
    # included, escapes intact) is kept as a single token so '#', ',' and
    # runs of spaces inside it survive
    def _tokenize_line(self, line: str) -> list[str]:
        tokens = []
        current = []
        in_string = False
        i = 0
        while i < len(line):
            ch = line[i]
            if in_string:
                current.append(ch)
                if ch == "\\" and i + 1 < len(line):  # keep escaped char, incl. \"
                    current.append(line[i + 1])
                    i += 1
                elif ch == '"':
                    in_string = False
            elif ch == "#":
                break
            elif ch == '"':
                in_string = True
                current.append(ch)
            elif ch in " \t,":
                if current:
                    tokens.append(''.join(current))
                    current = []
            else:
                current.append(ch)
            i += 1
        if current:
            tokens.append(''.join(current))
        return tokens

    # Adds an error of ParseError class
    def _add_error(self, line_number: int, line_text: str, message: str) -> None:
        self._errors.append(ParseError(line_number, line_text, message))

    # Checks whether label is reserved. If not, it store the label in the symbol table with the accompanying address
    def _register_label(self, label_name: str, address: int, line_number: int, line_text: str) -> bool:
        if label_name.lower() in RESERVED:
            self._add_error(line_number, line_text, f"'{label_name}' is a reserved word and cannot be used as a label")
            return False
        if label_name in self._symbol_table:
            self._add_error(line_number, line_text, f"Duplicate label: '{label_name}'")
            return False
        self._symbol_table[label_name] = address
        return True

    # ------------------------------------------------------------------
    # Private helpers — validation
    # ------------------------------------------------------------------

    # Validates an operand
    def _validate_operand(self, token: str, expected: str, line_number: int, line_text: str) -> bool:
        if expected == "reg":
            if not _REGISTER.fullmatch(token.lower()):
                self._add_error(line_number, line_text, f"Invalid register: '{token}'")
                return False
        elif expected == "imm":
            if not _IMMEDIATE.fullmatch(token):
                self._add_error(line_number, line_text, f"Invalid immediate: '{token}'")
                return False
        elif expected == "mem":
            match = _MEM_OPERAND.fullmatch(token)
            if not match:
                self._add_error(line_number, line_text, f"Invalid memory operand: '{token}'")
                return False
            if not _REGISTER.fullmatch(match.group(2).lower()):
                self._add_error(line_number, line_text, f"Invalid base register in memory operand: '{match.group(2)}'")
                return False
        elif expected == "label":
            if not _LABEL_REF.fullmatch(token) and not _IMMEDIATE.fullmatch(token):
                self._add_error(line_number, line_text, f"Invalid label or immediate: '{token}'")
                return False
            if _LABEL_REF.fullmatch(token) and token not in self._symbol_table:
                self._add_error(line_number, line_text, f"Undefined label: '{token}'")
                return False
        elif expected == "labelname":
            # a symbol only — numeric addresses are not accepted (la needs a label; li covers numerics)
            if not _LABEL_REF.fullmatch(token):
                self._add_error(line_number, line_text, f"Invalid label: '{token}'")
                return False
            if token not in self._symbol_table:
                self._add_error(line_number, line_text, f"Undefined label: '{token}'")
                return False
        return True

    # Validates all operands and used in the second pass
    def _validate_operands(self, mnemonic: str, operands: list[str], line_number: int, line_text: str) -> bool:
        def check(expected_count, *types):
            if len(operands) != expected_count:
                self._add_error(line_number, line_text, f"'{mnemonic}' expects {expected_count} operands, got {len(operands)}")
                return False
            return all(self._validate_operand(operands[i], types[i], line_number, line_text) for i in range(expected_count))

        if mnemonic in R_TYPE:
            return check(3, "reg", "reg", "reg")
        elif mnemonic in I_TYPE:
            return check(3, "reg", "reg", "imm")
        elif mnemonic in LOAD_TYPE:
            return check(2, "reg", "mem")
        elif mnemonic in STORE_TYPE:
            return check(2, "reg", "mem")
        elif mnemonic in BRANCH_TYPE:
            return check(3, "reg", "reg", "label")
        elif mnemonic in U_TYPE:
            return check(2, "reg", "imm")
        elif mnemonic in JAL_TYPE:
            return check(2, "reg", "label")
        elif mnemonic in JALR_TYPE:
            return check(3, "reg", "reg", "imm")
        elif mnemonic in NO_OPERAND:
            return check(0)
        elif mnemonic in LA_TYPE:
            return check(2, "reg", "labelname")
        elif mnemonic in LI_TYPE:
            return check(2, "reg", "imm")
        elif mnemonic in MV_TYPE:
            return check(2, "reg", "reg")
        elif mnemonic in J_TYPE:
            return check(1, "label")
        return True

    # ------------------------------------------------------------------
    # Private helpers — sizing and encoding
    # ------------------------------------------------------------------

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
                imm = parse_int(tokens[2])
                return 1 if -2048 <= imm <= 2047 else 2
            except (IndexError, ValueError):
                return 1
        return 1

    #  _data_size(line) returns the byte size of what _data_words would emit
    # used during the first pass to calculate data-label addresses.
    def _data_size(self, line: list[str]) -> int:
        try:
            return len(self._data_words(line)) * 4
        except ValueError:
            # invalid operands — the second pass reports the error; a rough
            # estimate here just keeps later label addresses defined
            return max(0, len(line) - 1) * 4

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

        if directive == ".word":
            words = []
            for v in parts[1:]:
                if not _IMMEDIATE.fullmatch(v):
                    raise ValueError(f"Invalid .word value: '{v}'")
                value = parse_int(v)
                # accept any signed or unsigned 32-bit form; anything wider
                # would be silently truncated by the mask below
                if not (-2147483648 <= value <= 4294967295):
                    raise ValueError(f".word value {v} out of 32-bit range")
                words.append(value & 0xFFFFFFFF)
            return words

        if directive in (".asciz", ".string", ".ascii"):
            # the tokenizer delivers a well-formed literal as ONE token,
            # quotes included; anything else (unquoted, unterminated,
            # trailing junk) is rejected here
            if (len(parts) != 2 or len(parts[1]) < 2
                    or not parts[1].startswith('"') or not parts[1].endswith('"')):
                raise ValueError(f"{directive} expects a single quoted string literal")
            byte_vals = self._parse_string(parts[1])
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