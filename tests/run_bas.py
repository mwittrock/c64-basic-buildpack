#!/usr/bin/env python3
"""
Local test runner for a single .bas file.

Usage:
    python run_bas.py <file.bas> [query_string]

Examples:
    python run_bas.py ../examples/fibonacci.bas "n=10"
    python run_bas.py ../examples/greet.bas "name=Alice"
    python run_bas.py ../examples/add.bas "a=7&b=3"
    python run_bas.py ../examples/hello.bas

Query string values are passed to the program as INPUT in the order they
appear.  Numeric values (integers and floats) are passed unquoted; anything
else is passed quoted so the BASIC INPUT statement receives it as a string.
"""

import sys
import os
from urllib.parse import parse_qsl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bridge'))

from basic_interpreter import BasicInterpreter, BasicError, BasicTimeout


def build_input_string(query_string: str) -> str:
    """
    Convert a query string into a comma-separated INPUT string.

    Values that parse as int or float are passed unquoted; all others are
    quoted so the BASIC runtime receives them as strings.
    """
    if not query_string:
        return ""

    parts = []
    for _key, value in parse_qsl(query_string, keep_blank_values=True):
        # Try integer first so "5" doesn't become "5.0"
        try:
            int(value)
            parts.append(value)
            continue
        except ValueError:
            pass

        try:
            float(value)
            parts.append(value)
            continue
        except ValueError:
            pass

        # String: wrap in quotes, escaping any embedded double-quotes
        escaped = value.replace('"', '""')
        parts.append(f'"{escaped}"')

    return ",".join(parts)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {os.path.basename(__file__)} <file.bas> [query_string]")
        sys.exit(1)

    bas_file = sys.argv[1]
    query_string = sys.argv[2] if len(sys.argv) > 2 else ""

    if not os.path.exists(bas_file):
        print(f"ERROR: File not found: {bas_file}")
        sys.exit(1)

    with open(bas_file, 'r') as f:
        source = f.read()

    input_string = build_input_string(query_string)

    # Print a small header so it's clear what's being run
    print(f"Program : {bas_file}")
    if query_string:
        print(f"Query   : {query_string}")
        print(f"Input   : {input_string}")
    print("-" * 40)

    interpreter = BasicInterpreter()

    try:
        interpreter.load_program(source)
    except BasicError as e:
        print(f"PARSE ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if input_string:
        interpreter.set_input(input_string)

    try:
        output = interpreter.run()
        print(output, end="")
    except BasicTimeout as e:
        print(f"TIMEOUT: {e}", file=sys.stderr)
        sys.exit(2)
    except BasicError as e:
        print(f"BASIC ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
