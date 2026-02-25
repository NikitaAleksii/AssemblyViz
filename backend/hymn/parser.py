from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ParseError:
    """Holds information about a single parse error."""
    line_number: int
    line_text: str
    message: str


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
        ...

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
        ...

    @property
    def errors(self) -> list[ParseError]:
        """All errors accumulated during the most recent call to parse()."""
        ...

    @property
    def symbol_table(self) -> dict[str, int]:
        """Label-to-address map built during the first pass.

        Available after a successful (or partial) parse for use by a
        debugger or error reporter.
        """
        ...

    # ------------------------------------------------------------------
    # Private helpers — first pass
    # ------------------------------------------------------------------

    def _first_pass(self, lines: list[str]) -> None:
        """Scan all lines and populate the symbol table.

        Does not encode any instructions. Records every label definition
        (e.g. 'LOOP:') and maps it to the address it will occupy in memory.

        Args:
            lines: Raw source lines, one per index.
        """
        ...

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
        ...

    def _encode_line(self, line_number: int, tokens: list[str]) -> int | None:
        """Encode a single tokenised line into one 8-bit machine word.

        Args:
            line_number: 1-based line number for error messages.
            tokens:      Non-empty list of tokens; tokens[0] is the mnemonic.

        Returns:
            Encoded 8-bit int, or None if the line contained an error.
        """
        ...

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
        ...

    def _is_label_definition(self, token: str) -> bool:
        """Return True if *token* is a label definition (ends with ':').

        Args:
            token: A single token string.
        """
        ...

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
        ...

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