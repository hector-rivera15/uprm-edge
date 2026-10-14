# UPRM-Edge

UPRM-Edge is a programming language that 

## Setup

Create and activate a virtual environment, then install the project dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Usage

Pass exactly one UPRM-Edge source file to the parser:

```bash
python parser.py prueba.uedge
```

## Repository layout

- `lexer.py` - PLY lexer definitions.
- `parser.py` - PLY parser and command-line entry point.
- `prueba.uedge` - small parser smoke-test program.
- `Programs/Valid Core Programs/` - public valid common-core examples.
- `Programs/Invalid Core Programs/` - public invalid-input examples.
- `Programs/Memory Track/` - public Memory-Aware track examples.
- `Instructions/` - assignment instruction images.
- `requirements.txt` - Python dependencies.

## Selected track

The selected extension is Memory-Aware. The public examples use annotations such as
`@memory(40kb)` before a function and array expressions such as
`array(int, 1000)`. At this stage, the parser must recognize the syntax; it does not
enforce memory budgets or execute programs.

## Validation

After installing dependencies, run the parser against the supplied `.uedge` files.
Valid programs should be accepted, while invalid programs should be rejected with a
line-aware error and no Python traceback.
