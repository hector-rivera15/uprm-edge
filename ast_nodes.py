"""Abstract syntax tree nodes for UPRM-Edge.

The parser produces these immutable nodes instead of loosely structured tuples.
Every node keeps the source line where it begins so later compiler stages can
report useful diagnostics.
"""

from dataclasses import dataclass
from typing import Optional, Tuple


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


__all__ = [
    "Annotation",
    "Assignment",
    "Binary",
    "Block",
    "BooleanLiteral",
    "Call",
    "Expression",
    "ExpressionStatement",
    "FloatLiteral",
    "For",
    "FunctionDeclaration",
    "Identifier",
    "If",
    "IntegerLiteral",
    "LetDeclaration",
    "MemoryAnnotation",
    "Node",
    "Print",
    "Program",
    "Return",
    "Statement",
    "StringLiteral",
    "Unary",
    "While",
]
