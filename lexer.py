import ply.lex as lex

tokens = ("PRINT",
          "INTEGER",
          "LPAREN",
          "RPAREN",
          "SEMICOLON",
          "LET",
          "IDENTIFIER",
          "ASSIGN",
          "PLUS",
          "MINUS",
          "TIMES",
          "DIVIDE"
          )

reserved = {
  "print": "PRINT",
  "let": "LET"
}

t_ASSIGN = r'='
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_SEMICOLON = r';'

def t_IDENTIFIER(t):
  r'[a-zA-Z_][a-zA-Z0-9_]*'
  t.type = reserved.get(t.value, "IDENTIFIER")
  return t

def t_INTEGER(t):
  r'\d+'
  t.value = int(t.value)
  return t

t_ignore = ' \t'

def t_newline(t):
  r'\n+'
  t.lexer.lineno += len(t.value) 

def t_error(t):
  raise ValueError(
    f"Error: illegal character {t.value[0]!r} at line {t.lineno}"
  )

lexer = lex.lex()