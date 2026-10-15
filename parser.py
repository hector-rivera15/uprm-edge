"""PLY parser for UPRM-Edge that produces :mod:`ast_nodes` values."""

import sys
from typing import Iterable, Optional, Tuple

import ply.yacc as yacc

from ast_nodes import (
    Assignment,
    Binary,
    Block,
    BooleanLiteral,
    Call,
    ExpressionStatement,
    FloatLiteral,
    For,
    FunctionDeclaration,
    Identifier,
    If,
    IntegerLiteral,
    LetDeclaration,
    MemoryAnnotation,
    Print,
    Program,
    Return,
    StringLiteral,
    Unary,
    While,
)
from lexer import lexer, tokens


start = "program"

precedence = (
    ("left", "EQ", "NE", "LT", "LE", "GT", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE", "MODULO"),
    ("right", "UMINUS"),
)


def _tuple(values: Iterable[object]) -> tuple:
    """Convert parser lists to immutable AST collections."""

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
    p[0] = LetDeclaration(
        name=p[2],
        initializer=p[4],
        line=p.lineno(1),
    )


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
    p[0] = If(
        condition=p[3],
        then_branch=p[5],
        else_branch=None,
        line=p.lineno(1),
    )


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
        raise ValueError(
            f"Error: unsupported annotation @{p[2]!s} at line {p.lineno(1)}"
        )
    p[0] = MemoryAnnotation(amount=p[4], unit=p[5], line=p.lineno(1))


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


def _eof_error_line() -> int:
    """Return the line of the nearest unmatched delimiter when available."""

    for symbol in reversed(getattr(parser, "symstack", ())):
        if getattr(symbol, "type", None) in {"LBRACE", "LPAREN"}:
            return getattr(symbol, "lineno", None) or lexer.lineno
    return lexer.lineno


def p_error(p):
    if p is None:
        raise ValueError(f"Error: unexpected end of file at line {_eof_error_line()}")

    raise ValueError(f"Error: unexpected token {p.value!r} at line {p.lineno}")


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
        print("Usage: python parser.py <file>.uedge")
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
