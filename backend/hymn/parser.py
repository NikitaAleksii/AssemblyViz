from __future__ import annotations
import re
from dataclasses import dataclass, field
from hymn.instructions import INSTRUCTIONS, OperandType


@dataclass
class ParseError:
    """Holds information about a single parse error."""
    line_number: int
    line_text: str
    message: str


# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------
_LABEL_DEF = re.compile(r'^[A-Z_][A-Z0-9_]*:$')    # e.g.  LOOP:
_DECIMAL   = re.compile(r'^[0-9]+$')                # e.g.  5  31
_LABEL_REF = re.compile(r'^[A-Z_][A-Z0-9_]*$')     # e.g.  LOOP  (no colon)


class Parser:
    """Assembles HYMN source text into a list of 8-bit machine words.

    Usage:
        parser = Parser()
        words = parser.parse(source_text)
        machine.load_program(words)

    If assembly fails, parser.errors will be non-empty and parse() returns None.
    """

    def __init__(self) -> None:
        """Initialise the parser with an empty symbol table and error list."""
        self._errorLst = []
        self._symbolDict = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, source: str) -> list[int] | None:

        """Assemble *source* into a list of 8-bit instruction words.

        Runs a two-pass assembly: first pass builds the symbol table,
        second pass encodes each instruction.

        Args:
            source: Multi-line HYMN assembly source text.

        Returns:
            A list of ints (one per instruction) on success, or None if
            any errors were encountered. Check self.errors for details.
        """
        self._errorLst   = []  # reset errors list back to empty list
        self._symbolDict = {}  # reset symbol dictionary to empty dictionary

        parsedLines = source.splitlines()

        self._first_pass(parsedLines)
        words = self._second_pass(parsedLines)

        if self._errorLst:
            return None
        return words

    @property
    def errors(self) -> list[ParseError]:
        """All errors accumulated during the most recent call to parse()."""
        return self._errorLst

    @property
    def symbol_table(self) -> dict[str, int]:
        """Label-to-address map built during the first pass.

        Available after a successful (or partial) parse for use by a
        debugger or error reporter.
        """
        return self._symbolDict

    # ------------------------------------------------------------------
    # Private helpers — first pass
    # ------------------------------------------------------------------

    def _first_pass(self, lines: list[str]) -> None:

        """Scan all lines and populate the symbol table.

        Does not encode any instructions. Records every label definition
        (e.g. 'LOOP:') and maps it to the address it will occupy in memory.

        Args:
            lines: Raw source lines, one per index."""

        address = 0

        for index, line in enumerate(lines):

            tokens = self._tokenize_line(line)
            if tokens == []:
                continue
            token = tokens[0]
            isLabel = self._is_label_definition(token)

            if isLabel:
                label_name = token.rstrip(':')
                self._symbolDict[label_name] = address
                if len(tokens) > 1:  # e.g. LOOP: ADD 3 must still increment address
                    address += 1
            else:
                address += 1

    # ------------------------------------------------------------------
    # Private helpers — second pass
    # ------------------------------------------------------------------

    def _second_pass(self, lines: list[str]) -> list[int]:
        """Encode every instruction into an 8-bit word.

        Uses the symbol table built by _first_pass to resolve label operands.

        Args:
            lines: Raw source lines, one per index.

        Returns:
            List of encoded instruction words.
        """
        words = []

        for index, line in enumerate(lines):
            tokens = self._tokenize_line(line)
            if tokens == []:
                continue

            # If line starts with a label, strip it and check for an instruction
            # on the same line (e.g. "LOOP: ADD 5")
            if self._is_label_definition(tokens[0]):
                tokens = tokens[1:]
                if not tokens:
                    continue  # label-only line — no instruction to encode

            word = self._encode_line(index + 1, tokens)
            if word is not None:
                words.append(word)

        return words

    def _encode_line(self, line_number: int, tokens: list[str]) -> int | None:
        """Encode a single tokenised line into one 8-bit machine word.

        8-bit layout:  [ opcode (3 bits) | operand (5 bits) ]

        Args:
            line_number: 1-based line number for error messages.
            tokens:      Non-empty list of tokens; tokens[0] is the mnemonic.

        Returns:
            Encoded 8-bit int, or None if the line contained an error.
        """
        mnemonic = tokens[0]

        if mnemonic not in INSTRUCTIONS:
            self._add_error(line_number, ' '.join(tokens),
                            f"Unknown mnemonic: '{mnemonic}'")
            return None

        instr = INSTRUCTIONS[mnemonic]

        if instr.operand_count == 0:
            if len(tokens) != 1:
                self._add_error(line_number, ' '.join(tokens),
                                f"'{mnemonic}' takes no operands")
                return None
            return instr.opcode << 5  # lower 5 bits are 0

        # All current HYMN instructions with operands take exactly one ADDRESS
        if len(tokens) != 2:
            self._add_error(line_number, ' '.join(tokens),
                            f"'{mnemonic}' expects 1 operand, got {len(tokens) - 1}")
            return None

        operand = self._resolve_operand(tokens[1], line_number)
        if operand is None:
            return None

        return (instr.opcode << 5) | operand

    # ------------------------------------------------------------------
    # Private helpers — tokenisation
    # ------------------------------------------------------------------

    def _tokenize_line(self, raw_line: str) -> list[str]:
        """Strip comments and whitespace; split into tokens.

        Removes everything after a ';', strips leading/trailing whitespace,
        normalises to upper case, and splits on whitespace.

        Args:
            raw_line: One raw line of source text.

        Returns:
            List of token strings (may be empty for blank/comment lines).
        """
        line = raw_line.split(';')[0]  # drop comment
        line = line.strip().upper()
        if not line:
            return []
        return line.split()

    def _is_label_definition(self, token: str) -> bool:
        """Return True if *token* is a label definition (ends with ':').

        Uses _LABEL_DEF regex: must start with a letter/underscore,
        contain only alphanumeric/underscore characters, and end with ':'.

        Args:
            token: A single token string.
        """
        return bool(_LABEL_DEF.fullmatch(token))

    def _resolve_operand(self, token: str, line_number: int) -> int | None:
        """Resolve an operand token to an integer address.

        The operand may be a decimal integer literal or a label name.
        Adds a ParseError and returns None if the label is undefined or
        the value is out of the valid 5-bit range (0–31).

        Args:
            token:       The operand token string.
            line_number: For error reporting.

        Returns:
            Integer address (0–31), or None on error.
        """
        if _DECIMAL.fullmatch(token):
            value = int(token)
        elif _LABEL_REF.fullmatch(token):
            if token not in self._symbolDict:
                self._add_error(line_number, token,
                                f"Undefined label: '{token}'")
                return None
            value = self._symbolDict[token]
        else:
            self._add_error(line_number, token,
                            f"Invalid operand: '{token}'")
            return None

        if not (0 <= value <= 31):
            self._add_error(line_number, token,
                            f"Operand {value} out of range (0–31)")
            return None

        return value

    # ------------------------------------------------------------------
    # Private helpers — error reporting
    # ------------------------------------------------------------------

    def _add_error(self, line_number: int, raw_line: str, message: str) -> None:

        """Record a ParseError for later inspection via self.errors.

        Args:
            line_number: 1-based line number.
            raw_line:    The original source line.
            message:     Human-readable description of the problem.
        """
        self._errorLst.append(ParseError(line_number, raw_line, message))
