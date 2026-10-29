import unittest

from ParserLexer import (
    Assignment,
    Binary,
    Block,
    Call,
    FunctionDeclaration,
    Identifier,
    If,
    IntegerLiteral,
    LetDeclaration,
    MemoryAnnotation,
    Print,
    Program,
    Return,
    While,
    parse_source,
)


class AstStructureTests(unittest.TestCase):
    def test_program_and_statements_retain_source_lines(self):
        declaration = LetDeclaration(
            name="answer",
            initializer=IntegerLiteral(value=42, line=1),
            line=1,
        )
        program = Program(statements=(declaration,), line=1)

        self.assertIsInstance(program, Program)
        self.assertEqual(program.line, 1)
        self.assertEqual(program.statements, (declaration,))
        self.assertEqual(program.statements[0].initializer.value, 42)

    def test_expression_nodes_have_stable_shapes(self):
        expression = Binary(
            operator="+",
            left=Identifier(name="a", line=3),
            right=IntegerLiteral(value=2, line=3),
            line=3,
        )

        self.assertEqual(expression.operator, "+")
        self.assertEqual(expression.left.name, "a")
        self.assertEqual(expression.right.value, 2)

    def test_control_flow_functions_calls_and_memory_annotations_are_composable(self):
        body = Block(
            statements=(
                Print(
                    expression=Call(
                        callee=Identifier(name="array", line=4),
                        arguments=(IntegerLiteral(value=10, line=4),),
                        line=4,
                    ),
                    line=4,
                ),
                Return(value=Identifier(name="buffer", line=5), line=5),
            ),
            line=4,
        )
        function = FunctionDeclaration(
            name="read",
            parameters=("size",),
            body=body,
            annotations=(MemoryAnnotation(amount=40, unit="kb", line=3),),
            line=3,
        )
        conditional = If(
            condition=Identifier(name="ready", line=8),
            then_branch=body,
            else_branch=Block(statements=(), line=10),
            line=8,
        )
        loop = While(
            condition=Identifier(name="ready", line=12),
            body=body,
            line=12,
        )
        assignment = Assignment(
            name="ready",
            value=Identifier(name="done", line=14),
            line=14,
        )
        program = Program(
            statements=(function, conditional, loop, assignment),
            line=3,
        )

        self.assertEqual(program.statements[0].annotations[0].unit, "kb")
        self.assertIs(program.statements[1].then_branch, body)
        self.assertIs(program.statements[2].body, body)
        self.assertEqual(program.statements[3].name, "ready")

    def test_parser_returns_ast_nodes_instead_of_tuples(self):
        program = parse_source("let answer = 40 + 2;\nprint(answer);\n")

        self.assertIsInstance(program, Program)
        self.assertIsInstance(program.statements[0], LetDeclaration)
        self.assertIsInstance(program.statements[0].initializer, Binary)
        self.assertIsInstance(program.statements[1], Print)
        self.assertIsInstance(program.statements[1].expression, Identifier)
        self.assertEqual(program.statements[0].line, 1)
        self.assertEqual(program.statements[1].line, 2)


if __name__ == "__main__":
    unittest.main()
