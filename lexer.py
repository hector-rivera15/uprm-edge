import ast

import ply.lex as lex

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

# Keywords and booleans, checked inside t_IDENTIFIER.
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


# Function rules match in order, so longer tokens go first ("//" before "/").
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


# Before INTEGER so "3.14" is one token.
def t_FLOAT(t):
    r"(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+"
    t.value = float(t.value)
    return t


def t_STRING(t):
    r'"([^"\\\r\n]|\\[^\r\n])*"'
    # Removes the quotes and resolves escapes like \n.
    try:
        t.value = ast.literal_eval(t.value)
    except (SyntaxError, ValueError) as error:
        raise ValueError(
            f"LEXICAL error: malformed string literal at line {t.lineno}"
        ) from error
    return t


# Opening quote with no closing quote on the line.
def t_UNTERMINATED_STRING(t):
    r'"([^"\\\r\n]|\\[^\r\n])*(?:\r\n|\r|\n|$)'
    raise ValueError(
        f"LEXICAL error: unterminated string literal at line {t.lineno}"
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


# Single-character tokens.
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
    # "\r\n" counts as one line break.
    t.lexer.lineno += len(t.value) - t.value.count("\r\n")


# Unknown character: raise so the parser can report it with its line.
def t_error(t):
    raise ValueError(
        f"LEXICAL error: illegal character {t.value[0]!r} at line {t.lineno}"
    )


lexer = lex.lex()
