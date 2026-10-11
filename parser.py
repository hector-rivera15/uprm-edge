import ply.yacc as yacc
from lexer import tokens, lexer

start = "program"

def p_program(p):
    'program : statements'
    p[0] = p[1]

def p_statements_single(p):
    'statements : statement'
    p[0] = [p[1]]

def p_statements_multiple(p):
    'statements : statements statement'
    p[0] = p[1] + [p[2]]

def p_statement_print(p):
    'statement : PRINT LPAREN expression RPAREN SEMICOLON'
    p[0] = ("print", p[3])

def p_expression_integer(p):
    'expression : INTEGER'
    p[0] = p[1]

def p_error(p):
    if p is None:
        raise ValueError(
            f"Error: unexpected end of file at line {lexer.lineno}"
        )

    raise ValueError(
        f"Error: unexpected token {p.value!r} at line {p.lineno}"
    )


parser = yacc.yacc()

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python parser.py <file>.uedge")
        raise SystemExit(1)

    try:
        with open(sys.argv[1], "r", encoding="utf-8") as archivo:
            codigo = archivo.read()

        lexer.lineno = 1
        resultado = parser.parse(codigo, lexer=lexer)
        print("Parse successful")

    except (ValueError, OSError) as error:
        print(error)
        raise SystemExit(1)