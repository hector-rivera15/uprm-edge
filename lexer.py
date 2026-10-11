import ply.lex as lex

tokens = ("PRINT",
          "INTEGER",
          "LPAREN",
          "RPAREN",
          "SEMICOLON"
          )

t_PRINT = r'print'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_SEMICOLON = r';'

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