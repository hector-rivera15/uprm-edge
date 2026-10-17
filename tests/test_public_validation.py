import unittest
from pathlib import Path

from ParserLexer import lexer, parser


ROOT = Path(__file__).resolve().parents[1]
PROGRAMS = ROOT / "Programs"


# Runs the lexer on a string and returns all tokens.
def lex_source(source):
    lexer.lineno = 1
    lexer.input(source)
    result = []
    while token := lexer.token():
        result.append(token)
    return result


class PublicProgramValidationTests(unittest.TestCase):
    # Valid programs must lex cleanly and use every core token type.
    def test_valid_core_programs_lex_without_errors(self):
        paths = sorted((PROGRAMS / "Valid Core Programs").glob("*.uedge"))
        observed_types = set()

        for path in paths:
            with self.subTest(program=path.name):
                observed_types.update(
                    token.type for token in lex_source(path.read_text(encoding="utf-8"))
                )

        self.assertEqual(len(paths), 8)
        self.assertTrue(
            {
                "LET",
                "FUNC",
                "IF",
                "ELSE",
                "WHILE",
                "FOR",
                "RETURN",
                "PRINT",
                "IDENTIFIER",
                "INTEGER",
                "FLOAT",
                "BOOLEAN",
                "STRING",
                "ASSIGN",
                "PLUS",
                "MINUS",
                "TIMES",
                "DIVIDE",
                "MODULO",
                "EQ",
                "NE",
                "LT",
                "GT",
                "LE",
                "GE",
                "LPAREN",
                "RPAREN",
                "LBRACE",
                "RBRACE",
                "COMMA",
                "SEMICOLON",
            }.issubset(observed_types)
        )

    # Literals get the right type/value; "iffy" stays an identifier, not "if".
    def test_literal_values_and_reserved_word_boundaries(self):
        result = lex_source(
            'let value = 12; let pi = 3.14; let ready = true; '
            'let text = "edge\\n"; let iffy = false; let ratio = 1e3;'
        )
        literal_tokens = [
            (token.type, token.value)
            for token in result
            if token.type
            in {"INTEGER", "FLOAT", "BOOLEAN", "STRING", "IDENTIFIER"}
        ]

        self.assertEqual(
            literal_tokens,
            [
                ("IDENTIFIER", "value"),
                ("INTEGER", 12),
                ("IDENTIFIER", "pi"),
                ("FLOAT", 3.14),
                ("IDENTIFIER", "ready"),
                ("BOOLEAN", True),
                ("IDENTIFIER", "text"),
                ("STRING", "edge\n"),
                ("IDENTIFIER", "iffy"),
                ("BOOLEAN", False),
                ("IDENTIFIER", "ratio"),
                ("FLOAT", 1000.0),
            ],
        )

    # A bad escape like "\u" must report a malformed string with its line.
    def test_malformed_string_escape_is_reported(self):
        with self.assertRaisesRegex(
            ValueError, r"^Error: malformed string at line 2$"
        ):
            lex_source('let value = 1;\nprint("\\u");')

    # Invalid programs must report the correct line for lexical errors.
    def test_public_lexical_errors_include_the_source_line(self):
        cases = (
            ("01_illegal_character.uedge", "let y = x $ 3;", "unexpected token"),
            ("04_unterminated_string.uedge", 'print("hello);', "malformed string"),
        )
        invalid_programs = PROGRAMS / "Invalid Core Programs"

        for filename, source_fragment, message in cases:
            with self.subTest(program=filename):
                source = (invalid_programs / filename).read_text(encoding="utf-8")
                expected_line = next(
                    number
                    for number, line in enumerate(source.splitlines(), start=1)
                    if source_fragment in line
                )
                with self.assertRaisesRegex(
                    ValueError,
                    rf"^Error: {message}.* at line {expected_line}$",
                ):
                    lex_source(source)

    # Every valid core program must parse. Fails until the parser is complete.
    def test_valid_core_programs_parse(self):
        self.assert_programs_parse(PROGRAMS / "Valid Core Programs")

    # Memory track programs are syntactically valid (the budget is checked in
    # Subproject 2). Fails until the track syntax is added.
    def test_memory_track_programs_parse(self):
        self.assert_programs_parse(PROGRAMS / "Memory Track")

    def assert_programs_parse(self, folder):
        paths = sorted(folder.glob("*.uedge"))
        self.assertTrue(paths)

        for path in paths:
            with self.subTest(program=path.name):
                lexer.lineno = 1
                parser.parse(path.read_text(encoding="utf-8"), lexer=lexer)

    # Invalid programs must report the correct line for syntax errors.
    def test_public_syntax_errors_are_located(self):
        # (file, line where the error should be reported)
        cases = (
            ("02_missing_semicolon.uedge", 3),
            ("05_annotation_missing_argument.uedge", 3),
            ("06_missing_paren.uedge", 3),
        )
        invalid_programs = PROGRAMS / "Invalid Core Programs"

        for filename, expected_line in cases:
            with self.subTest(program=filename):
                source = (invalid_programs / filename).read_text(encoding="utf-8")
                lexer.lineno = 1
                with self.assertRaisesRegex(
                    ValueError,
                    rf"^Error: .+ at line {expected_line}$",
                ):
                    parser.parse(source, lexer=lexer)

    def test_unclosed_block_reports_expected_message(self):
        source = (
            PROGRAMS
            / "Invalid Core Programs"
            / "03_unbalanced_braces.uedge"
        ).read_text(encoding="utf-8")

        lexer.lineno = 1
        with self.assertRaisesRegex(
            ValueError, r"^Error: missing closing '\}'$"
        ):
            parser.parse(source, lexer=lexer)

    def test_bare_memory_annotation_reports_the_annotation_line(self):
        source = "func before() {}\n@memory\nfunc after() {}\n"

        lexer.lineno = 1
        with self.assertRaisesRegex(
            ValueError,
            r"^Error: malformed @memory annotation at line 2$",
        ):
            parser.parse(source, lexer=lexer)


if __name__ == "__main__":
    unittest.main()
