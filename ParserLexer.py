"""Self-contained UPRM-Edge parser for the Moodle submission field.

This file intentionally contains the lexer, AST definitions, parser grammar,
and command-line entry point in one place. It can be copied into Moodle and
run as a single submitted source file.
"""

import ast as python_ast
import sys
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

import ply.lex as lex
import ply.yacc as yacc


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


@dataclass(frozen=True)
class Program(Node):
    statements: Tuple[Statement, ...]
    line: Optional[int] = None


@dataclass(frozen=True)
class Block(Statement):
    statements: Tuple[Statement, ...]
    line: Optional[int] = None


@dataclass(frozen=True)
class LetDeclaration(Statement):
    name: str
    initializer: Expression
    line: Optional[int] = None


@dataclass(frozen=True)
class Assignment(Statement):
    name: str
    value: Expression
    line: Optional[int] = None


@dataclass(frozen=True)
class Print(Statement):
    expression: Expression
    line: Optional[int] = None


@dataclass(frozen=True)
class ExpressionStatement(Statement):
    expression: Expression
    line: Optional[int] = None


@dataclass(frozen=True)
class Return(Statement):
    value: Optional[Expression] = None
    line: Optional[int] = None


@dataclass(frozen=True)
class If(Statement):
    condition: Expression
    then_branch: Block
    else_branch: Optional[Block] = None
    line: Optional[int] = None


@dataclass(frozen=True)
class While(Statement):
    condition: Expression
    body: Block
    line: Optional[int] = None


@dataclass(frozen=True)
class For(Statement):
    initializer: Optional[Statement]
    condition: Optional[Expression]
    update: Optional[Statement]
    body: Block
    line: Optional[int] = None


@dataclass(frozen=True)
class FunctionDeclaration(Statement):
    name: str
    parameters: Tuple[str, ...]
    body: Block
    annotations: Tuple[Annotation, ...] = ()
    line: Optional[int] = None


@dataclass(frozen=True)
class MemoryAnnotation(Annotation):
    amount: int
    unit: str
    line: Optional[int] = None


@dataclass(frozen=True)
class Identifier(Expression):
    name: str
    line: Optional[int] = None


@dataclass(frozen=True)
class IntegerLiteral(Expression):
    value: int
    line: Optional[int] = None


@dataclass(frozen=True)
class FloatLiteral(Expression):
    value: float
    line: Optional[int] = None


@dataclass(frozen=True)
class BooleanLiteral(Expression):
    value: bool
    line: Optional[int] = None


@dataclass(frozen=True)
class StringLiteral(Expression):
    value: str
    line: Optional[int] = None


@dataclass(frozen=True)
class Unary(Expression):
    operator: str
    operand: Expression
    line: Optional[int] = None


@dataclass(frozen=True)
class Binary(Expression):
    operator: str
    left: Expression
    right: Expression
    line: Optional[int] = None


@dataclass(frozen=True)
class Call(Expression):
    callee: Expression
    arguments: Tuple[Expression, ...]
    line: Optional[int] = None


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


def _column(source: str, lexpos: int) -> int:
    line_start = max(source.rfind("\n", 0, lexpos), source.rfind("\r", 0, lexpos)) + 1
    return lexpos - line_start + 1


def _line_end_column(source: str, line: int) -> int:
    lines = source.splitlines()
    if 1 <= line <= len(lines):
        return len(lines[line - 1]) + 1
    return _column(source, len(source))


def _error(message: str, line: int, column: int, suggestion: str) -> ValueError:
    return ValueError(
        f"Error: {message} at line {line}, character {column}\n"
        f"Suggestion: {suggestion.rstrip('.')} at line {line}, "
        f"character {column}."
    )


def _is_memory_annotation_error() -> bool:
    stack = getattr(parser, "symstack", ())
    return any(
        getattr(symbol, "type", None) == "IDENTIFIER"
        and getattr(symbol, "value", None) == "memory"
        for symbol in stack
    ) and any(getattr(symbol, "type", None) == "AT" for symbol in stack)


def t_COMMENT(t):
    r"//[^\r\n]*"


def t_EQ(t):
    r"=="
    return t


def t_NE(t):
    r"!="
    return t


def t_LE(t):
    r"<="
    return t


def t_GE(t):
    r">="
    return t


def t_FLOAT(t):
    r"(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+"
    t.value = float(t.value)
    return t


def t_STRING(t):
    r'"([^"\\\r\n]|\\[^\r\n])*"'
    try:
        t.value = python_ast.literal_eval(t.value)
    except (SyntaxError, ValueError) as error:
        raise _error(
            "malformed string",
            t.lineno,
            _column(t.lexer.lexdata, t.lexpos),
            'use a valid escape sequence and close the string.',
        ) from error
    return t


def t_UNTERMINATED_STRING(t):
    r'"([^"\\\r\n]|\\[^\r\n])*(?:\r\n|\r|\n|$)'
    raise _error(
        "malformed string",
        t.lineno,
        _column(t.lexer.lexdata, t.lexpos),
        'close the string with a matching `"`.',
    )


def t_INTEGER(t):
    r"\d+"
    t.value = int(t.value)
    return t


def t_IDENTIFIER(t):
    r"[a-zA-Z_][a-zA-Z0-9_]*"
    t.type = reserved.get(t.value, "IDENTIFIER")
    if t.type == "BOOLEAN":
        t.value = t.value == "true"
    return t


t_ASSIGN = r"="
t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"
t_MODULO = r"%"
t_LT = r"<"
t_GT = r">"
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LBRACE = r"\{"
t_RBRACE = r"\}"
t_COMMA = r","
t_SEMICOLON = r";"
t_AT = r"@"

t_ignore = " \t\f\v"


def t_newline(t):
    r"(?:\r\n|\r|\n)+"
    t.lexer.lineno += len(t.value) - t.value.count("\r\n")


def t_error(t):
    raise _error(
        f"unexpected token ‘{t.value[0]}’",
        t.lineno,
        _column(t.lexer.lexdata, t.lexpos),
        f"remove {t.value[0]!r} or replace it with a valid UPRM-Edge operator.",
    )


lexer = lex.lex()


# ---------------------------------------------------------------------------
# Parser


start = "program"

precedence = (
    ("left", "EQ", "NE", "LT", "LE", "GT", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE", "MODULO"),
    ("right", "UMINUS"),
)


def _tuple(values: Iterable[object]) -> tuple:
    return tuple(values)


def p_program(p):
    "program : statements_opt"
    statements = _tuple(p[1])
    line = statements[0].line if statements else None
    p[0] = Program(statements=statements, line=line)


def p_statements_opt_empty(p):
    "statements_opt : empty"
    p[0] = []


def p_statements_opt_nonempty(p):
    "statements_opt : statements"
    p[0] = p[1]


def p_statements_single(p):
    "statements : statement"
    p[0] = [p[1]]


def p_statements_multiple(p):
    "statements : statements statement"
    p[0] = p[1] + [p[2]]


def p_block(p):
    "block : LBRACE statements_opt RBRACE"
    p[0] = Block(statements=_tuple(p[2]), line=p.lineno(1))


def p_statement_declaration(p):
    "statement : LET IDENTIFIER ASSIGN expression SEMICOLON"
    p[0] = LetDeclaration(name=p[2], initializer=p[4], line=p.lineno(1))


def p_statement_assignment(p):
    "statement : IDENTIFIER ASSIGN expression SEMICOLON"
    p[0] = Assignment(name=p[1], value=p[3], line=p.lineno(1))


def p_statement_print(p):
    "statement : PRINT LPAREN expression RPAREN SEMICOLON"
    p[0] = Print(expression=p[3], line=p.lineno(1))


def p_statement_expression(p):
    "statement : expression SEMICOLON"
    p[0] = ExpressionStatement(expression=p[1], line=p[1].line)


def p_statement_return_value(p):
    "statement : RETURN expression SEMICOLON"
    p[0] = Return(value=p[2], line=p.lineno(1))


def p_statement_return_empty(p):
    "statement : RETURN SEMICOLON"
    p[0] = Return(value=None, line=p.lineno(1))


def p_statement_if(p):
    "statement : IF LPAREN expression RPAREN block"
    p[0] = If(condition=p[3], then_branch=p[5], line=p.lineno(1))


def p_statement_if_else(p):
    "statement : IF LPAREN expression RPAREN block ELSE block"
    p[0] = If(
        condition=p[3],
        then_branch=p[5],
        else_branch=p[7],
        line=p.lineno(1),
    )


def p_statement_while(p):
    "statement : WHILE LPAREN expression RPAREN block"
    p[0] = While(condition=p[3], body=p[5], line=p.lineno(1))


def p_statement_for(p):
    "statement : FOR LPAREN for_initializer_opt SEMICOLON for_condition_opt SEMICOLON for_update_opt RPAREN block"
    p[0] = For(
        initializer=p[3],
        condition=p[5],
        update=p[7],
        body=p[9],
        line=p.lineno(1),
    )


def p_for_initializer_opt_empty(p):
    "for_initializer_opt : empty"
    p[0] = None


def p_for_initializer_declaration(p):
    "for_initializer_opt : LET IDENTIFIER ASSIGN expression"
    p[0] = LetDeclaration(name=p[2], initializer=p[4], line=p.lineno(1))


def p_for_initializer_assignment(p):
    "for_initializer_opt : IDENTIFIER ASSIGN expression"
    p[0] = Assignment(name=p[1], value=p[3], line=p.lineno(1))


def p_for_condition_opt_empty(p):
    "for_condition_opt : empty"
    p[0] = None


def p_for_condition_opt_expression(p):
    "for_condition_opt : expression"
    p[0] = p[1]


def p_for_update_opt_empty(p):
    "for_update_opt : empty"
    p[0] = None


def p_for_update_assignment(p):
    "for_update_opt : IDENTIFIER ASSIGN expression"
    p[0] = Assignment(name=p[1], value=p[3], line=p.lineno(1))


def p_for_update_expression(p):
    "for_update_opt : expression"
    p[0] = ExpressionStatement(expression=p[1], line=p[1].line)


def p_statement_function(p):
    "statement : annotations_opt FUNC IDENTIFIER LPAREN parameters_opt RPAREN block"
    p[0] = FunctionDeclaration(
        name=p[3],
        parameters=_tuple(p[5]),
        body=p[7],
        annotations=_tuple(p[1]),
        line=p.lineno(2),
    )


def p_annotations_opt_empty(p):
    "annotations_opt : empty"
    p[0] = []


def p_annotations_opt_annotations(p):
    "annotations_opt : annotations"
    p[0] = p[1]


def p_annotations_single(p):
    "annotations : annotation"
    p[0] = [p[1]]


def p_annotations_multiple(p):
    "annotations : annotations annotation"
    p[0] = p[1] + [p[2]]


def p_annotation_memory(p):
    "annotation : AT IDENTIFIER LPAREN INTEGER IDENTIFIER RPAREN"
    if p[2] != "memory":
        raise _error(
            f"unsupported annotation @{p[2]!s}",
            p.lineno(1),
            _column(lexer.lexdata, p.lexpos(1)),
            "use the supported @memory(numberunit) annotation.",
        )
    p[0] = MemoryAnnotation(amount=p[4], unit=p[5], line=p.lineno(1))


def p_annotation_missing_arguments(p):
    "annotation : AT IDENTIFIER"
    if p[2] == "memory":
        raise _error(
            "malformed @memory annotation",
            p.lineno(1),
            _column(lexer.lexdata, p.lexpos(1)),
            "write @memory(numberunit), for example @memory(40kb).",
        )
    raise _error(
        f"unsupported annotation @{p[2]!s}",
        p.lineno(1),
        _column(lexer.lexdata, p.lexpos(1)),
        "use the supported @memory(numberunit) annotation.",
    )


def p_parameters_opt_empty(p):
    "parameters_opt : empty"
    p[0] = []


def p_parameters_opt_parameters(p):
    "parameters_opt : parameters"
    p[0] = p[1]


def p_parameters_single(p):
    "parameters : IDENTIFIER"
    p[0] = [p[1]]


def p_parameters_multiple(p):
    "parameters : parameters COMMA IDENTIFIER"
    p[0] = p[1] + [p[3]]


def p_expression_identifier(p):
    "expression : IDENTIFIER"
    p[0] = Identifier(name=p[1], line=p.lineno(1))


def p_expression_integer(p):
    "expression : INTEGER"
    p[0] = IntegerLiteral(value=p[1], line=p.lineno(1))


def p_expression_float(p):
    "expression : FLOAT"
    p[0] = FloatLiteral(value=p[1], line=p.lineno(1))


def p_expression_boolean(p):
    "expression : BOOLEAN"
    p[0] = BooleanLiteral(value=p[1], line=p.lineno(1))


def p_expression_string(p):
    "expression : STRING"
    p[0] = StringLiteral(value=p[1], line=p.lineno(1))


def p_expression_group(p):
    "expression : LPAREN expression RPAREN"
    p[0] = p[2]


def p_expression_unary_minus(p):
    "expression : MINUS expression %prec UMINUS"
    p[0] = Unary(operator="-", operand=p[2], line=p.lineno(1))


def p_expression_binary(p):
    """expression : expression PLUS expression
                    | expression MINUS expression
                    | expression TIMES expression
                    | expression DIVIDE expression
                    | expression MODULO expression
                    | expression EQ expression
                    | expression NE expression
                    | expression LT expression
                    | expression GT expression
                    | expression LE expression
                    | expression GE expression"""
    p[0] = Binary(operator=p[2], left=p[1], right=p[3], line=p[1].line)


def p_expression_call(p):
    "expression : IDENTIFIER LPAREN arguments_opt RPAREN"
    callee = Identifier(name=p[1], line=p.lineno(1))
    p[0] = Call(callee=callee, arguments=_tuple(p[3]), line=p.lineno(1))


def p_arguments_opt_empty(p):
    "arguments_opt : empty"
    p[0] = []


def p_arguments_opt_arguments(p):
    "arguments_opt : arguments"
    p[0] = p[1]


def p_arguments_single(p):
    "arguments : expression"
    p[0] = [p[1]]


def p_arguments_multiple(p):
    "arguments : arguments COMMA expression"
    p[0] = p[1] + [p[3]]


def p_empty(p):
    "empty :"
    p[0] = None


def _last_terminal():
    for symbol in reversed(getattr(parser, "symstack", ())):
        if getattr(symbol, "type", None) in tokens:
            return symbol
    return None


def _expected_tokens():
    state_stack = getattr(parser, "statestack", ())
    if not state_stack:
        return set()
    actions = getattr(parser, "action", {}).get(state_stack[-1], {})
    return {token_type for token_type, action in actions.items() if action}


def _unclosed_delimiters():
    delimiters = []
    matching = {"RPAREN": "LPAREN", "RBRACE": "LBRACE"}
    for symbol in getattr(parser, "symstack", ()):
        symbol_type = getattr(symbol, "type", None)
        if symbol_type in {"LPAREN", "LBRACE"}:
            delimiters.append(symbol_type)
        elif symbol_type in matching and delimiters and delimiters[-1] == matching[symbol_type]:
            delimiters.pop()
    return delimiters


def _eof_location(source: str):
    lines = source.splitlines()
    for line_number in range(len(lines), 0, -1):
        if lines[line_number - 1].strip():
            return line_number, len(lines[line_number - 1]) + 1
    return 1, 1


def p_error(p):
    source = getattr(lexer, "lexdata", "")
    previous = _last_terminal()
    expected = _expected_tokens()
    unclosed = _unclosed_delimiters()

    if (
        p is not None
        and p.type == "RPAREN"
        and expected == {"IDENTIFIER"}
        and _is_memory_annotation_error()
    ):
        raise _error(
            "malformed @memory annotation",
            p.lineno,
            _column(source, p.lexpos),
            "add the unit, for example @memory(40kb).",
        )

    if p is not None and p.type == "RPAREN" and expected == {"INTEGER"}:
        raise _error(
            "malformed @memory annotation",
            p.lineno,
            _column(source, p.lexpos),
            "add an integer amount and unit, for example @memory(40kb).",
        )

    if "RPAREN" in expected and "LPAREN" in unclosed:
        if p is not None:
            line = p.lineno
            column = _column(source, p.lexpos)
        else:
            line, column = _eof_location(source)
        raise _error(
            "missing closing ')'",
            line,
            column,
            "insert ')' before the token shown.",
        )

    if "RBRACE" in expected and "LBRACE" in unclosed:
        if p is not None:
            line = p.lineno
            column = _column(source, p.lexpos)
        else:
            line, column = _eof_location(source)
        raise _error(
            "missing closing '}'",
            line,
            column,
            "add '}' to close the block.",
        )

    if "SEMICOLON" in expected:
        if p is not None and (
            previous is None or previous.lineno == p.lineno
        ):
            line = p.lineno
            column = _column(source, p.lexpos)
        elif previous is not None:
            line = previous.lineno
            column = _line_end_column(source, line)
        else:
            line = lexer.lineno
            column = _line_end_column(source, line)
        raise _error(
            "expected ‘;’",
            line,
            column,
            "add ';' at the end of the statement.",
        )

    if p is None:
        line, column = _eof_location(source)
        raise _error(
            "unexpected end of file",
            line,
            column,
            "complete the statement or add the missing closing delimiter.",
        )

    raise _error(
        f"unexpected token ‘{p.value}’",
        p.lineno,
        _column(source, p.lexpos),
        f"remove {p.value!r} or replace it with the token expected here.",
    )


parser = yacc.yacc(
    write_tables=False,
    debug=False,
    errorlog=yacc.NullLogger(),
)


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
            parse_source(source_file.read())
    except (OSError, ValueError) as error:
        print(error)
        return 1

    print("Parse successful")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
