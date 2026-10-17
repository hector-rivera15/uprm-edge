"""Self-contained UPRM-Edge parser for the Moodle submission field.

This file intentionally contains the lexer, AST definitions, parser grammar,
and command-line entry point in one place. It can be copied into Moodle and
run as a single submitted source file.
"""

import ast as python_ast
import re
import sys
from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# AST nodes


class Node:
    """Marker base class for every AST node."""


class Statement(Node):
    """Marker base class for statement nodes."""


class Expression(Node):
    """Marker base class for expression nodes."""


class Annotation(Node):
    """Marker base class for declaration annotations."""


class Program(Node):
    def __init__(self, statements: Tuple[Statement, ...], line: Optional[int] = None):
        self.statements = statements
        self.line = line


class Block(Statement):
    def __init__(self, statements: Tuple[Statement, ...], line: Optional[int] = None):
        self.statements = statements
        self.line = line


class LetDeclaration(Statement):
    def __init__(
        self, name: str, initializer: Expression, line: Optional[int] = None
    ):
        self.name = name
        self.initializer = initializer
        self.line = line


class Assignment(Statement):
    def __init__(self, name: str, value: Expression, line: Optional[int] = None):
        self.name = name
        self.value = value
        self.line = line


class Print(Statement):
    def __init__(self, expression: Expression, line: Optional[int] = None):
        self.expression = expression
        self.line = line


class ExpressionStatement(Statement):
    def __init__(self, expression: Expression, line: Optional[int] = None):
        self.expression = expression
        self.line = line


class Return(Statement):
    def __init__(
        self, value: Optional[Expression] = None, line: Optional[int] = None
    ):
        self.value = value
        self.line = line


class If(Statement):
    def __init__(
        self,
        condition: Expression,
        then_branch: Block,
        else_branch: Optional[Block] = None,
        line: Optional[int] = None,
    ):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
        self.line = line


class While(Statement):
    def __init__(self, condition: Expression, body: Block, line: Optional[int] = None):
        self.condition = condition
        self.body = body
        self.line = line


class For(Statement):
    def __init__(
        self,
        initializer: Optional[Statement],
        condition: Optional[Expression],
        update: Optional[Statement],
        body: Block,
        line: Optional[int] = None,
    ):
        self.initializer = initializer
        self.condition = condition
        self.update = update
        self.body = body
        self.line = line


class FunctionDeclaration(Statement):
    def __init__(
        self,
        name: str,
        parameters: Tuple[str, ...],
        body: Block,
        annotations: Tuple[Annotation, ...] = (),
        line: Optional[int] = None,
    ):
        self.name = name
        self.parameters = parameters
        self.body = body
        self.annotations = annotations
        self.line = line


class MemoryAnnotation(Annotation):
    def __init__(self, amount: int, unit: str, line: Optional[int] = None):
        self.amount = amount
        self.unit = unit
        self.line = line


class Identifier(Expression):
    def __init__(self, name: str, line: Optional[int] = None):
        self.name = name
        self.line = line


class IntegerLiteral(Expression):
    def __init__(self, value: int, line: Optional[int] = None):
        self.value = value
        self.line = line


class FloatLiteral(Expression):
    def __init__(self, value: float, line: Optional[int] = None):
        self.value = value
        self.line = line


class BooleanLiteral(Expression):
    def __init__(self, value: bool, line: Optional[int] = None):
        self.value = value
        self.line = line


class StringLiteral(Expression):
    def __init__(self, value: str, line: Optional[int] = None):
        self.value = value
        self.line = line


class Unary(Expression):
    def __init__(self, operator: str, operand: Expression, line: Optional[int] = None):
        self.operator = operator
        self.operand = operand
        self.line = line


class Binary(Expression):
    def __init__(
        self, operator: str, left: Expression, right: Expression, line: Optional[int] = None
    ):
        self.operator = operator
        self.left = left
        self.right = right
        self.line = line


class Call(Expression):
    def __init__(
        self, callee: Expression, arguments: Tuple[Expression, ...], line: Optional[int] = None
    ):
        self.callee = callee
        self.arguments = arguments
        self.line = line


# ---------------------------------------------------------------------------
# Lexer


tokens = (
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
    "AT",
    "UNTERMINATED_STRING",
)

reserved = {
    "let": "LET",
    "func": "FUNC",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "for": "FOR",
    "return": "RETURN",
    "print": "PRINT",
    "true": "BOOLEAN",
    "false": "BOOLEAN",
}


_FLOAT_PATTERN = re.compile(
    r"(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+"
)
_INTEGER_PATTERN = re.compile(r"\d+")
_IDENTIFIER_PATTERN = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")
_TWO_CHARACTER_TOKENS = {
    "==": "EQ",
    "!=": "NE",
    "<=": "LE",
    ">=": "GE",
}
_ONE_CHARACTER_TOKENS = {
    "=": "ASSIGN",
    "+": "PLUS",
    "-": "MINUS",
    "*": "TIMES",
    "/": "DIVIDE",
    "%": "MODULO",
    "<": "LT",
    ">": "GT",
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    ",": "COMMA",
    ";": "SEMICOLON",
    "@": "AT",
}


class LexToken:
    def __init__(self, token_type: str, value: object, lineno: int):
        self.type = token_type
        self.value = value
        self.lineno = lineno


class Lexer:
    def __init__(self):
        self.lineno = 1
        self._source = ""
        self._position = 0

    def input(self, source: str) -> None:
        self._source = source
        self._position = 0

    def token(self) -> Optional[LexToken]:
        source = self._source
        length = len(source)

        while self._position < length:
            char = source[self._position]

            if char in " \t\f\v":
                self._position += 1
                continue

            if char == "\r" or char == "\n":
                if char == "\r" and self._position + 1 < length and source[
                    self._position + 1
                ] == "\n":
                    self._position += 2
                else:
                    self._position += 1
                self.lineno += 1
                continue

            if source.startswith("//", self._position):
                newline = self._position
                while newline < length and source[newline] not in "\r\n":
                    newline += 1
                self._position = newline
                continue

            line = self.lineno

            if char == '"':
                start = self._position
                self._position += 1
                while self._position < length:
                    current = source[self._position]
                    if current == "\r" or current == "\n":
                        raise ValueError(
                            f"Error: malformed string at line {line}"
                        )
                    if current == "\\":
                        if self._position + 1 >= length:
                            self._position = length
                            break
                        if source[self._position + 1] in "\r\n":
                            raise ValueError(
                                f"Error: malformed string at line {line}"
                            )
                        self._position += 2
                        continue
                    if current == '"':
                        self._position += 1
                        literal = source[start : self._position]
                        try:
                            value = python_ast.literal_eval(literal)
                        except (SyntaxError, ValueError) as error:
                            raise ValueError(
                                f"Error: malformed string at line {line}"
                            ) from error
                        return LexToken("STRING", value, line)
                    self._position += 1
                raise ValueError(
                    f"Error: malformed string at line {line}"
                )

            match = _FLOAT_PATTERN.match(source, self._position)
            if match is not None:
                self._position = match.end()
                return LexToken("FLOAT", float(match.group()), line)

            match = _INTEGER_PATTERN.match(source, self._position)
            if match is not None:
                self._position = match.end()
                return LexToken("INTEGER", int(match.group()), line)

            match = _IDENTIFIER_PATTERN.match(source, self._position)
            if match is not None:
                self._position = match.end()
                value = match.group()
                token_type = reserved.get(value, "IDENTIFIER")
                if token_type == "BOOLEAN":
                    value = value == "true"
                return LexToken(token_type, value, line)

            pair = source[self._position : self._position + 2]
            if pair in _TWO_CHARACTER_TOKENS:
                self._position += 2
                return LexToken(_TWO_CHARACTER_TOKENS[pair], pair, line)

            if char in _ONE_CHARACTER_TOKENS:
                self._position += 1
                return LexToken(_ONE_CHARACTER_TOKENS[char], char, line)

            raise ValueError(
                f"Error: unexpected token ‘{char}’ at line {line}"
            )

        return None


lexer = Lexer()


# ---------------------------------------------------------------------------
# Parser


start = "program"

precedence = (
    ("left", "EQ", "NE", "LT", "LE", "GT", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE", "MODULO"),
    ("right", "UMINUS"),
)


_BINARY_PRECEDENCE = {
    "EQ": 1,
    "NE": 1,
    "LT": 1,
    "LE": 1,
    "GT": 1,
    "GE": 1,
    "PLUS": 2,
    "MINUS": 2,
    "TIMES": 3,
    "DIVIDE": 3,
    "MODULO": 3,
}
_BINARY_OPERATORS = {
    "EQ": "==",
    "NE": "!=",
    "LT": "<",
    "LE": "<=",
    "GT": ">",
    "GE": ">=",
    "PLUS": "+",
    "MINUS": "-",
    "TIMES": "*",
    "DIVIDE": "/",
    "MODULO": "%",
}


class Parser:
    def parse(self, source: str, lexer: Optional[Lexer] = None) -> Program:
        self.lexer = lexer or globals()["lexer"]
        self.lexer.input(source)
        self._open_delimiters = []
        self._current = self.lexer.token()

        statements = []
        while self._current is not None:
            statements.append(self._parse_statement())

        line = statements[0].line if statements else None
        return Program(statements=tuple(statements), line=line)

    def _advance(self) -> Optional[LexToken]:
        previous = self._current
        if previous is not None:
            if previous.type in {"LPAREN", "LBRACE"}:
                self._open_delimiters.append((previous.type, previous.lineno))
            elif previous.type in {"RPAREN", "RBRACE"}:
                opening = "LPAREN" if previous.type == "RPAREN" else "LBRACE"
                if self._open_delimiters and self._open_delimiters[-1][0] == opening:
                    self._open_delimiters.pop()
        self._current = self.lexer.token()
        return previous

    def _accept(self, token_type: str) -> Optional[LexToken]:
        if self._current is not None and self._current.type == token_type:
            return self._advance()
        return None

    def _expect(self, token_type: str, error_line: Optional[int] = None) -> LexToken:
        token = self._accept(token_type)
        if token is None:
            line = (
                error_line
                if error_line is not None
                else self._current.lineno
                if self._current is not None
                else self._missing_delimiter_line(token_type)
            )
            if token_type == "SEMICOLON":
                raise ValueError(f"Error: expected ‘;’ at line {line}")
            if token_type == "RPAREN":
                raise ValueError(f"Error: missing closing ')' at line {line}")
            if token_type == "RBRACE":
                raise ValueError("Error: missing closing '}'")
            self._syntax_error()
        return token

    def _missing_delimiter_line(self, token_type: str) -> int:
        opening_type = {"RPAREN": "LPAREN", "RBRACE": "LBRACE"}.get(token_type)
        if opening_type is not None:
            for delimiter_type, line in reversed(self._open_delimiters):
                if delimiter_type == opening_type:
                    return line
        return self.lexer.lineno

    def _syntax_error(self) -> None:
        if self._current is None:
            line = (
                self._open_delimiters[-1][1]
                if self._open_delimiters
                else self.lexer.lineno
            )
            raise ValueError(f"Error: unexpected end of file at line {line}")
        raise ValueError(
            f"Error: unexpected token ‘{self._current.value}’ "
            f"at line {self._current.lineno}"
        )

    def _parse_statement(self) -> Statement:
        if self._current.type == "AT":
            annotations = self._parse_annotations()
            if self._current is None or self._current.type != "FUNC":
                self._syntax_error()
            return self._parse_function(annotations)

        token_type = self._current.type
        if token_type == "LET":
            return self._parse_declaration(require_semicolon=True)
        if token_type == "FUNC":
            return self._parse_function(())
        if token_type == "IDENTIFIER":
            if self._peek_type() == "ASSIGN":
                return self._parse_assignment(require_semicolon=True)
        elif token_type == "PRINT":
            return self._parse_print()
        elif token_type == "RETURN":
            return self._parse_return()
        elif token_type == "IF":
            return self._parse_if()
        elif token_type == "WHILE":
            return self._parse_while()
        elif token_type == "FOR":
            return self._parse_for()

        expression = self._parse_expression()
        self._expect("SEMICOLON", error_line=expression.line)
        return ExpressionStatement(expression=expression, line=expression.line)

    def _peek_type(self) -> Optional[str]:
        position = self.lexer._position
        line = self.lexer.lineno
        token = self.lexer.token()
        self.lexer._position = position
        self.lexer.lineno = line
        return token.type if token is not None else None

    def _parse_declaration(self, require_semicolon: bool) -> LetDeclaration:
        keyword = self._expect("LET")
        name = self._expect("IDENTIFIER")
        self._expect("ASSIGN")
        initializer = self._parse_expression()
        if require_semicolon:
            self._expect("SEMICOLON", error_line=keyword.lineno)
        return LetDeclaration(name=name.value, initializer=initializer, line=keyword.lineno)

    def _parse_assignment(self, require_semicolon: bool) -> Assignment:
        name = self._expect("IDENTIFIER")
        self._expect("ASSIGN")
        value = self._parse_expression()
        if require_semicolon:
            self._expect("SEMICOLON", error_line=name.lineno)
        return Assignment(name=name.value, value=value, line=name.lineno)

    def _parse_print(self) -> Print:
        keyword = self._expect("PRINT")
        self._expect("LPAREN")
        expression = self._parse_expression()
        self._expect("RPAREN")
        self._expect("SEMICOLON", error_line=keyword.lineno)
        return Print(expression=expression, line=keyword.lineno)

    def _parse_return(self) -> Return:
        keyword = self._expect("RETURN")
        if self._current is not None and self._current.type != "SEMICOLON":
            value = self._parse_expression()
        else:
            value = None
        self._expect("SEMICOLON", error_line=keyword.lineno)
        return Return(value=value, line=keyword.lineno)

    def _parse_if(self) -> If:
        keyword = self._expect("IF")
        self._expect("LPAREN")
        condition = self._parse_expression()
        self._expect("RPAREN")
        then_branch = self._parse_block()
        else_branch = None
        if self._accept("ELSE") is not None:
            else_branch = self._parse_block()
        return If(
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
            line=keyword.lineno,
        )

    def _parse_while(self) -> While:
        keyword = self._expect("WHILE")
        self._expect("LPAREN")
        condition = self._parse_expression()
        self._expect("RPAREN")
        body = self._parse_block()
        return While(condition=condition, body=body, line=keyword.lineno)

    def _parse_for(self) -> For:
        keyword = self._expect("FOR")
        self._expect("LPAREN")

        initializer = None
        if self._current is not None and self._current.type != "SEMICOLON":
            if self._current.type == "LET":
                initializer = self._parse_declaration(require_semicolon=False)
            elif (
                self._current.type == "IDENTIFIER"
                and self._peek_type() == "ASSIGN"
            ):
                initializer = self._parse_assignment(require_semicolon=False)
            else:
                self._syntax_error()
        self._expect("SEMICOLON", error_line=keyword.lineno)

        condition = None
        if self._current is not None and self._current.type != "SEMICOLON":
            condition = self._parse_expression()
        self._expect("SEMICOLON", error_line=keyword.lineno)

        update = None
        if self._current is not None and self._current.type != "RPAREN":
            if (
                self._current.type == "IDENTIFIER"
                and self._peek_type() == "ASSIGN"
            ):
                update = self._parse_assignment(require_semicolon=False)
            else:
                expression = self._parse_expression()
                update = ExpressionStatement(expression=expression, line=expression.line)
        self._expect("RPAREN")

        body = self._parse_block()
        return For(
            initializer=initializer,
            condition=condition,
            update=update,
            body=body,
            line=keyword.lineno,
        )

    def _parse_function(
        self, annotations: Tuple[Annotation, ...]
    ) -> FunctionDeclaration:
        keyword = self._expect("FUNC")
        name = self._expect("IDENTIFIER")
        self._expect("LPAREN")
        parameters = []
        if self._current is not None and self._current.type != "RPAREN":
            parameters.append(self._expect("IDENTIFIER").value)
            while self._accept("COMMA") is not None:
                parameters.append(self._expect("IDENTIFIER").value)
        self._expect("RPAREN")
        body = self._parse_block()
        return FunctionDeclaration(
            name=name.value,
            parameters=tuple(parameters),
            body=body,
            annotations=annotations,
            line=keyword.lineno,
        )

    def _parse_annotations(self) -> Tuple[Annotation, ...]:
        annotations = []
        while self._current is not None and self._current.type == "AT":
            at = self._advance()
            name = self._expect("IDENTIFIER")
            if self._current is None or self._current.type != "LPAREN":
                if name.value == "memory":
                    raise ValueError(
                        f"Error: malformed @memory annotation at line {at.lineno}"
                    )
                raise ValueError(
                    f"Error: unsupported annotation @{name.value!s} at line {at.lineno}"
                )

            self._advance()
            if self._current is None or self._current.type != "INTEGER":
                if name.value == "memory":
                    raise ValueError(
                        f"Error: malformed @memory annotation at line {at.lineno}"
                    )
                self._syntax_error()
            amount = self._advance()

            if self._current is None or self._current.type != "IDENTIFIER":
                if name.value == "memory":
                    raise ValueError(
                        f"Error: malformed @memory annotation at line {at.lineno}"
                    )
                self._syntax_error()
            unit = self._advance()
            if self._current is None or self._current.type != "RPAREN":
                if name.value == "memory":
                    raise ValueError(
                        f"Error: malformed @memory annotation at line {at.lineno}"
                    )
                self._expect("RPAREN")
            self._expect("RPAREN")

            if name.value != "memory":
                raise ValueError(
                    f"Error: unsupported annotation @{name.value!s} at line {at.lineno}"
                )
            annotations.append(
                MemoryAnnotation(amount=amount.value, unit=unit.value, line=at.lineno)
            )
        return tuple(annotations)

    def _parse_block(self) -> Block:
        opening = self._expect("LBRACE")
        statements = []
        while self._current is not None and self._current.type != "RBRACE":
            statements.append(self._parse_statement())
        self._expect("RBRACE")
        return Block(statements=tuple(statements), line=opening.lineno)

    def _parse_expression(self, minimum_precedence: int = 1) -> Expression:
        if self._current is not None and self._current.type == "MINUS":
            operator = self._advance()
            left = Unary(
                operator="-",
                operand=self._parse_expression(4),
                line=operator.lineno,
            )
        else:
            left = self._parse_primary()

        while (
            self._current is not None
            and self._current.type in _BINARY_PRECEDENCE
            and _BINARY_PRECEDENCE[self._current.type] >= minimum_precedence
        ):
            operator_type = self._current.type
            operator = _BINARY_OPERATORS[operator_type]
            precedence_level = _BINARY_PRECEDENCE[operator_type]
            self._advance()
            right = self._parse_expression(precedence_level + 1)
            left = Binary(operator=operator, left=left, right=right, line=left.line)
        return left

    def _parse_primary(self) -> Expression:
        if self._current is None:
            self._syntax_error()

        token_type = self._current.type
        if token_type == "IDENTIFIER":
            identifier = self._advance()
            callee = Identifier(name=identifier.value, line=identifier.lineno)
            if self._accept("LPAREN") is not None:
                arguments = []
                if self._current is not None and self._current.type != "RPAREN":
                    arguments.append(self._parse_expression())
                    while self._accept("COMMA") is not None:
                        arguments.append(self._parse_expression())
                self._expect("RPAREN")
                return Call(
                    callee=callee,
                    arguments=tuple(arguments),
                    line=identifier.lineno,
                )
            return callee

        literal_types = {
            "INTEGER": IntegerLiteral,
            "FLOAT": FloatLiteral,
            "BOOLEAN": BooleanLiteral,
            "STRING": StringLiteral,
        }
        if token_type in literal_types:
            token = self._advance()
            return literal_types[token_type](value=token.value, line=token.lineno)

        if self._accept("LPAREN") is not None:
            expression = self._parse_expression()
            self._expect("RPAREN")
            return expression

        self._syntax_error()


parser = Parser()


def parse_source(source: str) -> Program:
    """Parse source text and return its AST."""

    lexer.lineno = 1
    result = parser.parse(source, lexer=lexer)
    if not isinstance(result, Program):
        raise ValueError("Error: parser did not produce a program AST")
    return result


def main(argv: Optional[Tuple[str, ...]] = None) -> int:
    """Run the parser command-line interface."""

    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1:
        print("Usage: python ParserLexer.py <file>.uedge")
        return 1

    try:
        with open(arguments[0], "r", encoding="utf-8") as source_file:
            source = source_file.read()
    except OSError as error:
        print(error)
        return 1

    try:
        parse_source(source)
    except ValueError as error:
        print(error)
        return 0

    print("Parsed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
