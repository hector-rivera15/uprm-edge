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
                [sys.executable, str(copied_parser), str(copied_program)],
                cwd=temporary_directory,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Parse successful")
        self.assertNotIn("Traceback", result.stderr)

    def test_submission_does_not_import_local_project_modules(self):
        source = SUBMISSION.read_text(encoding="utf-8")

        self.assertNotIn("from ast_nodes import", source)
        self.assertNotIn("from lexer import", source)


if __name__ == "__main__":
    unittest.main()
