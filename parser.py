import ply.yacc as yacc
from lexer import tokens, lexer

start = "program"

precedence = (
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE")
)

def p_program(p):
    'program : statements'
    p[0] = p[1]

def p_statements_single(p):
    'statements : statement'
    p[0] = [p[1]]

def p_statements_multiple(p):
    'statements : statements statement'
    p[0] = p[1] + [p[2]]

def p_statement_declaration(p):
    'statement : LET IDENTIFIER ASSIGN expression SEMICOLON'
    p[0] = ("let", p[2], p[4])

def p_statement_assignment(p):
    'statement : IDENTIFIER ASSIGN expression SEMICOLON'
    p[0] = ("assign", p[1], p[3])

def p_expression_identifier(p):
    'expression : IDENTIFIER'
    p[0] = ("identifier", p[1])

def p_statement_print(p):
    'statement : PRINT LPAREN expression RPAREN SEMICOLON'
    p[0] = ("print", p[3])

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression'''
    p[0] = (p[2], p[1], p[3])

def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

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

/////////////////////////////new common core Parser/////////////////////////////
//1//
//basics expressions//
def p_expression_float(p):
    'expression : FLOAT'
    p[0] = p[1]

def p_expression_string(p):
    'expression : STRING'
    p[0] = p[1]

def p_expression_boolean(p):
    'expression : BOOLEAN'
    p[0] = p[1]

//more info//
def p_expression_comparison(p):
    'expression : expression LT expression
                  | expression GT expression
                  | expression GE expression
                  | expression LE expression
                  | expression EQ expression
                  | expression NE expression'
    p[0] = (p[2], p[1], p[3])

def p_expression_modulo(p):
    'expression : expression MODULO expression'
    p[0] = (p[2], p[1], p[3])

//functions//
def p_arguments_empty(p):
    'arguments : empty'
    p[0] = []

def p_arguments_single(p):
    'arguments : expression'
    p[0] = [p[1]]

def p_arguments_multiple(p):
    'arguments : arguments COMMA expression'
    p[0] = p[1] + [p[3]]

def p_expression_function(p):
    'expression : IDENTIFIER LPAREN arguments RPAREN'
    p[0] = ("call", p[1], p[3])

//2//
//statements//
def p_statement_return(p):
    'statement : RETURN expression SEMICOLON'
    p[0] = ("return", p[2])

def p_statement_if_else(p):
    '''statement : IF LPAREN expression RPAREN LBRACE statements RBRACE
                 ELSE LBRACE statements RBRACE'''
    p[0] = ("if_else", p[3], p[6], p[10])

def p_statement_while_loop(p):
    'statement : WHILE LPAREN expression RPAREN LBRACE statements RBRACE'
    p[0] = ("while", p[3], p[6])

//3//
//functions and for loops//
def p_statement_function(p):
    'statement : FUNC IDENTIFIER LPAREN parameters RPAREN LBRACE statements RBRACE'
    p[0] = ("function", p[2], p[4], p[7])

def p_expression_function_call(p):
    'expression : IDENTIFIER LPAREN arguments RPAREN'
    p[0] = ("call", p[1], p[3])

//for loops//

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