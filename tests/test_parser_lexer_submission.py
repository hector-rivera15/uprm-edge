import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "ParserLexer.py"
SAMPLE = ROOT / "prueba.uedge"


class ParserLexerSubmissionTests(unittest.TestCase):
    def test_submission_file_is_self_contained_when_copied(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_directory = Path(directory)
            copied_parser = temporary_directory / "ParserLexer.py"
            copied_program = temporary_directory / "program.uedge"
            shutil.copyfile(SUBMISSION, copied_parser)
            shutil.copyfile(SAMPLE, copied_program)

            result = subprocess.run(
                [sys.executable, "-S", str(copied_parser), str(copied_program)],
                cwd=temporary_directory,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Parsed successfully")
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_examples_match_expected_diagnostics(self):
        expected_outputs = {
            "01_illegal_character.uedge": "Error: unexpected token ‘$’ at line 4",
            "02_missing_semicolon.uedge": "Error: expected ‘;’ at line 3",
            "03_unbalanced_braces.uedge": "Error: missing closing '}'",
        }

        for filename, expected_output in expected_outputs.items():
            with self.subTest(program=filename):
                program = ROOT / "Programs" / "Invalid Core Programs" / filename
                result = subprocess.run(
                    [sys.executable, "-S", str(SUBMISSION), str(program)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), expected_output)
                self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_invalid_submission_reports_error_without_runtime_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_directory = Path(directory)
            copied_parser = temporary_directory / "ParserLexer.py"
            invalid_program = temporary_directory / "program.uedge"
            shutil.copyfile(SUBMISSION, copied_parser)
            invalid_program.write_text("let x = 1\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, "-S", str(copied_parser), str(invalid_program)],
                cwd=temporary_directory,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0)
        self.assertRegex(result.stdout, r"^Error: .+ at line \d+$")
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_submission_does_not_import_local_project_modules(self):
        source = SUBMISSION.read_text(encoding="utf-8")

        self.assertNotIn("from ast_nodes import", source)
        self.assertNotIn("from lexer import", source)


if __name__ == "__main__":
    unittest.main()
