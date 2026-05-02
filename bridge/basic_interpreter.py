"""
C64 BASIC Interpreter - Grammar-based implementation
Based on Commodore PET BASIC 2.0 BNF grammar

This is a complete rewrite using proper lexical analysis and recursive descent parsing.
"""

import re
import time
import math
import random
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum, auto
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# PETSCII <-> Unicode helpers
# ---------------------------------------------------------------------------
# C64 BASIC uses PETSCII codes, not ASCII/Unicode, for CHR$() and ASC().
# Codes 32-91 and 93 are identical to ASCII. Key differences:
#   92 → £ (pound sign, not backslash)
#   94 → ↑, 95 → ←, 96 → ─
#   205 → /  (SHIFT+M, maze diagonal)
#   206 → \  (SHIFT+N, maze diagonal)
# Codes not listed fall back to chr()/ord() (best-effort).

_PETSCII_TO_CHAR: dict[int, str] = {
    **{i: chr(i) for i in range(32, 92)},   # space … [  (same as ASCII)
    92:  '\u00a3',  # £
    93:  ']',
    94:  '\u2191',  # ↑
    95:  '\u2190',  # ←
    96:  '\u2500',  # ─
    **{i: chr(i) for i in range(97, 128)},  # lowercase / graphics (best-effort)
    160: ' ',       # shifted space
    205: '╱',  # ╱ SHIFT+M
    206: '╲',  # ╲ SHIFT+N
}

_CHAR_TO_PETSCII: dict[str, int] = {v: k for k, v in _PETSCII_TO_CHAR.items()}
# Ensure the primary (lowest-code) PETSCII value wins for any duplicate chars.
# Re-build in reverse so lower keys overwrite higher ones.
_CHAR_TO_PETSCII = {}
for _code in sorted(_PETSCII_TO_CHAR):
    _CHAR_TO_PETSCII[_PETSCII_TO_CHAR[_code]] = _code


def _petscii_chr(code: int) -> str:
    """Return the Unicode character for a PETSCII code."""
    return _PETSCII_TO_CHAR.get(code, chr(code))


def _petscii_asc(char: str) -> int:
    """Return the PETSCII code for a character."""
    if not char:
        return 0
    return _CHAR_TO_PETSCII.get(char[0], ord(char[0]))


class TokenType(Enum):
    """Token types for lexical analysis"""
    # Literals
    INTEGER = auto()
    REAL = auto()
    STRING = auto()
    
    # Identifiers
    ID = auto()
    FUNCTION_ID = auto()
    
    # Keywords
    DATA = auto()
    DEF = auto()
    DIM = auto()
    END = auto()
    FOR = auto()
    GOSUB = auto()
    GOTO = auto()
    IF = auto()
    INPUT = auto()
    LET = auto()
    NEXT = auto()
    PRINT = auto()
    READ = auto()
    REM = auto()
    RESTORE = auto()
    RETURN = auto()
    STEP = auto()
    STOP = auto()
    THEN = auto()
    TO = auto()
    
    # Built-in functions (need to be tokens for proper parsing)
    ABS = auto()
    ASC = auto()
    ATN = auto()
    CHR = auto()
    COS = auto()
    EXP = auto()
    INT = auto()
    LEFT = auto()
    LEN = auto()
    MID = auto()
    RIGHT = auto()
    RND = auto()
    SGN = auto()
    SIN = auto()
    SQR = auto()
    STR = auto()
    TAN = auto()
    VAL = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    POWER = auto()
    
    # Comparison
    EQ = auto()
    NE = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    
    # Logical
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    SEMICOLON = auto()
    COLON = auto()
    
    # Special
    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    """A lexical token"""
    type: TokenType
    value: Any
    line: int = 0
    column: int = 0


class BasicError(Exception):
    """Exception raised for BASIC program errors"""
    pass


class BasicTimeout(Exception):
    """Exception raised when program execution times out"""
    pass


class Lexer:
    """Tokenizer for BASIC source code"""
    
    # Keywords mapping
    KEYWORDS = {
        'DATA': TokenType.DATA,
        'DEF': TokenType.DEF,
        'DIM': TokenType.DIM,
        'END': TokenType.END,
        'FOR': TokenType.FOR,
        'GOSUB': TokenType.GOSUB,
        'GOTO': TokenType.GOTO,
        'IF': TokenType.IF,
        'INPUT': TokenType.INPUT,
        'LET': TokenType.LET,
        'NEXT': TokenType.NEXT,
        'PRINT': TokenType.PRINT,
        'READ': TokenType.READ,
        'REM': TokenType.REM,
        'RESTORE': TokenType.RESTORE,
        'RETURN': TokenType.RETURN,
        'STEP': TokenType.STEP,
        'STOP': TokenType.STOP,
        'THEN': TokenType.THEN,
        'TO': TokenType.TO,
        'AND': TokenType.AND,
        'OR': TokenType.OR,
        'NOT': TokenType.NOT,
        # Built-in functions
        'ABS': TokenType.ABS,
        'ASC': TokenType.ASC,
        'ATN': TokenType.ATN,
        'CHR$': TokenType.CHR,
        'COS': TokenType.COS,
        'EXP': TokenType.EXP,
        'INT': TokenType.INT,
        'LEFT$': TokenType.LEFT,
        'LEN': TokenType.LEN,
        'MID$': TokenType.MID,
        'RIGHT$': TokenType.RIGHT,
        'RND': TokenType.RND,
        'SGN': TokenType.SGN,
        'SIN': TokenType.SIN,
        'SQR': TokenType.SQR,
        'STR$': TokenType.STR,
        'TAN': TokenType.TAN,
        'VAL': TokenType.VAL,
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        
    def peek(self, offset: int = 0) -> str:
        """Look ahead at character without consuming it"""
        pos = self.pos + offset
        if pos < len(self.source):
            return self.source[pos]
        return '\0'
    
    def advance(self) -> str:
        """Consume and return current character"""
        if self.pos < len(self.source):
            char = self.source[self.pos]
            self.pos += 1
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            return char
        return '\0'
    
    def skip_whitespace(self):
        """Skip spaces and tabs (but not newlines)"""
        while self.peek() in ' \t':
            self.advance()
    
    def read_number(self) -> Token:
        """Read integer or real number"""
        start_col = self.column
        num_str = ''
        
        while self.peek().isdigit():
            num_str += self.advance()
        
        # Check for decimal point
        if self.peek() == '.' and self.peek(1).isdigit():
            num_str += self.advance()  # consume '.'
            while self.peek().isdigit():
                num_str += self.advance()
            return Token(TokenType.REAL, float(num_str), self.line, start_col)
        
        return Token(TokenType.INTEGER, int(num_str), self.line, start_col)
    
    def read_string(self) -> Token:
        """Read string literal"""
        start_col = self.column
        self.advance()  # skip opening quote
        
        string_val = ''
        while self.peek() != '"' and self.peek() != '\0' and self.peek() != '\n':
            string_val += self.advance()
        
        if self.peek() == '"':
            self.advance()  # skip closing quote
        
        return Token(TokenType.STRING, string_val, self.line, start_col)
    
    def read_identifier_or_keyword(self) -> Token:
        """Read identifier or keyword"""
        start_col = self.column
        id_str = ''
        
        # Read full alphabetic sequence first to check for keywords
        while self.peek().isalpha():
            id_str += self.advance()
        
        # Check for string functions ending in $
        if self.peek() == '$':
            test_str = id_str.upper() + '$'
            if test_str in self.KEYWORDS:
                id_str += self.advance()
                keyword_type = self.KEYWORDS.get(id_str.upper())
                return Token(keyword_type, id_str.upper(), self.line, start_col)
        
        # Check if it's a keyword (case insensitive)
        keyword_type = self.KEYWORDS.get(id_str.upper())
        if keyword_type:
            return Token(keyword_type, id_str.upper(), self.line, start_col)
        
        # Check for FN function (user-defined function name like FNMOD10)
        if id_str.upper().startswith('FN') and len(id_str) > 2:
            # This is a user-defined function name
            return Token(TokenType.FUNCTION_ID, id_str.upper(), self.line, start_col)
        
        # It's a variable name - only the first 2 characters are significant
        # (C64 BASIC allows names up to 80 chars but ignores chars beyond the 2nd)
        var_name = id_str[:2]  # First 2 alpha chars are the identity

        # If only 1 alpha char was read, the next char may be a digit that forms
        # the second significant character of the name (e.g. "A1" in "A1BXYZ")
        if len(id_str) == 1 and self.peek().isdigit():
            var_name += self.advance()

        # Discard any remaining alphanumeric chars (not significant in C64 BASIC)
        while self.peek().isalnum():
            self.advance()

        # Check for type suffix
        if self.peek() in '$%':
            var_name += self.advance()
        
        return Token(TokenType.ID, var_name.upper(), self.line, start_col)
    
    def read_remark(self) -> Token:
        """Read REM comment - consumes rest of line"""
        start_col = self.column
        # Skip 'REM' 
        self.advance()  # R
        self.advance()  # E
        self.advance()  # M
        if self.peek() == ' ':
            self.advance()
        
        # Read rest of line
        remark = ''
        while self.peek() not in '\n\r\0':
            remark += self.advance()
        
        return Token(TokenType.REM, remark, self.line, start_col)
    
    def tokenize(self) -> List[Token]:
        """Tokenize entire source into list of tokens"""
        tokens = []
        
        while self.pos < len(self.source):
            self.skip_whitespace()
            
            char = self.peek()
            
            # End of input
            if char == '\0':
                break
            
            # Newline
            if char == '\n':
                tokens.append(Token(TokenType.NEWLINE, '\n', self.line, self.column))
                self.advance()
                continue
            
            # Carriage return (treat as newline)
            if char == '\r':
                self.advance()
                if self.peek() == '\n':
                    self.advance()
                tokens.append(Token(TokenType.NEWLINE, '\n', self.line, self.column))
                continue
            
            # Numbers
            if char.isdigit():
                tokens.append(self.read_number())
                continue
            
            # Strings
            if char == '"':
                tokens.append(self.read_string())
                continue
            
            # Identifiers and keywords
            if char.isalpha():
                # Special case for REM
                if self.source[self.pos:self.pos+3].upper() == 'REM':
                    tokens.append(self.read_remark())
                    continue
                
                tokens.append(self.read_identifier_or_keyword())
                continue
            
            # Operators and punctuation
            if char == '+':
                tokens.append(Token(TokenType.PLUS, '+', self.line, self.column))
                self.advance()
            elif char == '-':
                tokens.append(Token(TokenType.MINUS, '-', self.line, self.column))
                self.advance()
            elif char == '*':
                tokens.append(Token(TokenType.MULTIPLY, '*', self.line, self.column))
                self.advance()
            elif char == '/':
                tokens.append(Token(TokenType.DIVIDE, '/', self.line, self.column))
                self.advance()
            elif char == '^':
                tokens.append(Token(TokenType.POWER, '^', self.line, self.column))
                self.advance()
            elif char == '(':
                tokens.append(Token(TokenType.LPAREN, '(', self.line, self.column))
                self.advance()
            elif char == ')':
                tokens.append(Token(TokenType.RPAREN, ')', self.line, self.column))
                self.advance()
            elif char == ',':
                tokens.append(Token(TokenType.COMMA, ',', self.line, self.column))
                self.advance()
            elif char == ';':
                tokens.append(Token(TokenType.SEMICOLON, ';', self.line, self.column))
                self.advance()
            elif char == ':':
                tokens.append(Token(TokenType.COLON, ':', self.line, self.column))
                self.advance()
            elif char == '=':
                tokens.append(Token(TokenType.EQ, '=', self.line, self.column))
                self.advance()
            elif char == '<':
                self.advance()
                if self.peek() == '>':
                    self.advance()
                    tokens.append(Token(TokenType.NE, '<>', self.line, self.column - 2))
                elif self.peek() == '=':
                    self.advance()
                    tokens.append(Token(TokenType.LE, '<=', self.line, self.column - 2))
                else:
                    tokens.append(Token(TokenType.LT, '<', self.line, self.column - 1))
            elif char == '>':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    tokens.append(Token(TokenType.GE, '>=', self.line, self.column - 2))
                else:
                    tokens.append(Token(TokenType.GT, '>', self.line, self.column - 1))
            else:
                raise BasicError(f"Unexpected character '{char}' at line {self.line}, column {self.column}")
        
        tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return tokens


# AST Node classes
@dataclass
class ASTNode:
    """Base class for AST nodes"""
    pass


@dataclass
class NumberNode(ASTNode):
    value: Union[int, float]


@dataclass  
class StringNode(ASTNode):
    value: str


@dataclass
class VariableNode(ASTNode):
    name: str
    indices: Optional[List[ASTNode]] = None  # For array access


@dataclass
class BinaryOpNode(ASTNode):
    op: TokenType
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryOpNode(ASTNode):
    op: TokenType
    operand: ASTNode


@dataclass
class FunctionCallNode(ASTNode):
    func_type: TokenType
    args: List[ASTNode]
    func_name: Optional[str] = None  # For user-defined functions (FN...)


@dataclass
class AssignmentNode(ASTNode):
    var_name: str
    indices: Optional[List[ASTNode]]
    expression: ASTNode


@dataclass
class PrintNode(ASTNode):
    items: List[Tuple[ASTNode, str]]  # (expression, separator)
    trailing_sep: Optional[str]  # None, ';', or ','


@dataclass
class InputNode(ASTNode):
    var_names: List[str]
    prompt: Optional[str] = None  # Optional prompt string (ignored in web service)


@dataclass
class IfNode(ASTNode):
    condition: ASTNode
    then_clause: Union[int, List[ASTNode]]  # line number or statements


@dataclass
class ForNode(ASTNode):
    var_name: str
    start: ASTNode
    end: ASTNode
    step: Optional[ASTNode]


@dataclass
class NextNode(ASTNode):
    var_names: List[str]


@dataclass
class GotoNode(ASTNode):
    target: ASTNode


@dataclass
class GosubNode(ASTNode):
    target: ASTNode


@dataclass
class ReturnNode(ASTNode):
    pass


@dataclass
class DimNode(ASTNode):
    var_name: str
    dimensions: List[ASTNode]


@dataclass
class DefNode(ASTNode):
    func_name: str
    param: str
    expression: ASTNode


@dataclass
class DataNode(ASTNode):
    values: List[Union[int, float, str]]


@dataclass
class ReadNode(ASTNode):
    var_names: List[str]


@dataclass
class RestoreNode(ASTNode):
    pass


@dataclass
class EndNode(ASTNode):
    pass


@dataclass
class StopNode(ASTNode):
    pass


@dataclass
class RemNode(ASTNode):
    text: str


class Parser:
    """Recursive descent parser for BASIC"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = tokens[0] if tokens else Token(TokenType.EOF, None)
    
    def advance(self):
        """Move to next token"""
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
            self.current_token = self.tokens[self.pos]
    
    def peek(self, offset: int = 1) -> Token:
        """Look ahead at token"""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return Token(TokenType.EOF, None)
    
    def expect(self, token_type: TokenType) -> Token:
        """Consume token of expected type or raise error"""
        if self.current_token.type != token_type:
            raise BasicError(f"Expected {token_type}, got {self.current_token.type} at line {self.current_token.line}")
        token = self.current_token
        self.advance()
        return token
    
    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types"""
        return self.current_token.type in token_types
    
    def parse_program(self) -> Dict[int, List[ASTNode]]:
        """Parse entire program into line number -> statements mapping"""
        program = {}
        
        while not self.match(TokenType.EOF):
            # Skip blank lines
            if self.match(TokenType.NEWLINE):
                self.advance()
                continue
            
            # Parse line: line_number statements NEWLINE
            if not self.match(TokenType.INTEGER):
                raise BasicError(f"Expected line number, got {self.current_token.type}")
            
            line_num = self.current_token.value
            self.advance()
            
            # Parse statements on this line
            statements = self.parse_statements()
            program[line_num] = statements
            
            # Expect newline or EOF
            if self.match(TokenType.NEWLINE):
                self.advance()
            elif not self.match(TokenType.EOF):
                raise BasicError(f"Expected newline after line {line_num}")
        
        return program
    
    def parse_statements(self) -> List[ASTNode]:
        """Parse colon-separated statements"""
        statements = []
        
        statements.append(self.parse_statement())
        
        while self.match(TokenType.COLON):
            self.advance()
            # Allow empty statement after colon
            if not self.match(TokenType.NEWLINE, TokenType.EOF):
                statements.append(self.parse_statement())
        
        return statements
    
    def parse_statement(self) -> ASTNode:
        """Parse a single statement"""
        
        # REM
        if self.match(TokenType.REM):
            text = self.current_token.value
            self.advance()
            return RemNode(text)
        
        # DEF FN
        if self.match(TokenType.DEF):
            self.advance()
            # In C64 BASIC: DEF FN name(param) = expression
            # "FN" will be tokenized as an ID (2-char variable)
            if not self.match(TokenType.ID) or self.current_token.value != 'FN':
                raise BasicError(f"Expected FN after DEF at line {self.current_token.line}")
            self.advance()
            # Now read the function name (another ID)
            if not self.match(TokenType.ID):
                raise BasicError(f"Expected function name after DEF FN at line {self.current_token.line}")
            func_name = 'FN' + self.current_token.value  # Combine FN with name
            self.advance()
            self.expect(TokenType.LPAREN)
            param = self.expect(TokenType.ID).value
            self.expect(TokenType.RPAREN)
            self.expect(TokenType.EQ)
            expression = self.parse_expression()
            return DefNode(func_name, param, expression)
        
        # PRINT
        if self.match(TokenType.PRINT):
            self.advance()
            return self.parse_print()
        
        # INPUT
        if self.match(TokenType.INPUT):
            self.advance()
            
            # Check for optional prompt string
            prompt = None
            if self.match(TokenType.STRING):
                prompt = self.current_token.value
                self.advance()
                # Expect semicolon or comma after prompt
                if self.match(TokenType.SEMICOLON, TokenType.COMMA):
                    self.advance()
                else:
                    raise BasicError(f"Expected ';' or ',' after INPUT prompt at line {self.current_token.line}")
            
            var_names = self.parse_id_list()
            return InputNode(var_names, prompt)
        
        # IF
        if self.match(TokenType.IF):
            self.advance()
            condition = self.parse_expression()
            self.expect(TokenType.THEN)
            
            # THEN can be followed by line number or statement(s)
            if self.match(TokenType.INTEGER):
                target = self.current_token.value
                self.advance()
                return IfNode(condition, target)
            else:
                # Parse all statements after THEN (until newline/colon at statement level)
                statements = []
                statements.append(self.parse_statement())
                
                # Continue parsing if there are more statements separated by colons
                while self.match(TokenType.COLON):
                    self.advance()
                    if not self.match(TokenType.NEWLINE, TokenType.EOF):
                        statements.append(self.parse_statement())
                
                return IfNode(condition, statements)
        
        # FOR
        if self.match(TokenType.FOR):
            self.advance()
            var_name = self.expect(TokenType.ID).value
            self.expect(TokenType.EQ)
            start = self.parse_expression()
            self.expect(TokenType.TO)
            end = self.parse_expression()
            
            step = None
            if self.match(TokenType.STEP):
                self.advance()
                step = self.parse_expression()
            
            return ForNode(var_name, start, end, step)
        
        # NEXT
        if self.match(TokenType.NEXT):
            self.advance()
            var_names = []
            if self.match(TokenType.ID):
                var_names = self.parse_id_list()
            return NextNode(var_names)
        
        # GOTO
        if self.match(TokenType.GOTO):
            self.advance()
            target = self.parse_expression()
            return GotoNode(target)
        
        # GOSUB
        if self.match(TokenType.GOSUB):
            self.advance()
            target = self.parse_expression()
            return GosubNode(target)
        
        # RETURN
        if self.match(TokenType.RETURN):
            self.advance()
            return ReturnNode()
        
        # DIM
        if self.match(TokenType.DIM):
            self.advance()
            var_name = self.expect(TokenType.ID).value
            self.expect(TokenType.LPAREN)
            dimensions = self.parse_expression_list()
            self.expect(TokenType.RPAREN)
            return DimNode(var_name, dimensions)
        
        # DATA
        if self.match(TokenType.DATA):
            self.advance()
            values = self.parse_constant_list()
            return DataNode(values)
        
        # READ
        if self.match(TokenType.READ):
            self.advance()
            var_names = self.parse_id_list()
            return ReadNode(var_names)
        
        # RESTORE
        if self.match(TokenType.RESTORE):
            self.advance()
            return RestoreNode()
        
        # END
        if self.match(TokenType.END):
            self.advance()
            return EndNode()
        
        # STOP
        if self.match(TokenType.STOP):
            self.advance()
            return StopNode()
        
        # LET (optional keyword)
        if self.match(TokenType.LET):
            self.advance()
        
        # Assignment: ID = expression or ID(indices) = expression
        if self.match(TokenType.ID):
            var_name = self.current_token.value
            self.advance()
            
            # Check for array subscript
            indices = None
            if self.match(TokenType.LPAREN):
                self.advance()
                indices = self.parse_expression_list()
                self.expect(TokenType.RPAREN)
            
            self.expect(TokenType.EQ)
            expr = self.parse_expression()
            
            return AssignmentNode(var_name, indices, expr)
        
        raise BasicError(f"Unexpected token in statement: {self.current_token.type} at line {self.current_token.line}")
    
    def parse_print(self) -> PrintNode:
        """Parse PRINT statement"""
        items = []
        trailing_sep = None
        
        # Empty PRINT
        if self.match(TokenType.NEWLINE, TokenType.COLON, TokenType.EOF):
            return PrintNode([], None)
        
        while True:
            # Parse expression
            expr = self.parse_expression()
            
            # Check for separator
            sep = None
            if self.match(TokenType.SEMICOLON):
                sep = ';'
                self.advance()
            elif self.match(TokenType.COMMA):
                sep = ','
                self.advance()
            
            items.append((expr, sep))
            
            # If no separator, or we hit end of statement, stop
            if sep is None or self.match(TokenType.NEWLINE, TokenType.COLON, TokenType.EOF):
                trailing_sep = sep
                break
        
        return PrintNode(items, trailing_sep)
    
    def parse_id_list(self) -> List[str]:
        """Parse comma-separated list of identifiers"""
        ids = []
        ids.append(self.expect(TokenType.ID).value)
        
        while self.match(TokenType.COMMA):
            self.advance()
            ids.append(self.expect(TokenType.ID).value)
        
        return ids
    
    def parse_constant_list(self) -> List[Union[int, float, str]]:
        """Parse comma-separated list of constants"""
        constants = []
        
        # Parse first constant
        if self.match(TokenType.INTEGER):
            constants.append(self.current_token.value)
            self.advance()
        elif self.match(TokenType.REAL):
            constants.append(self.current_token.value)
            self.advance()
        elif self.match(TokenType.STRING):
            constants.append(self.current_token.value)
            self.advance()
        else:
            raise BasicError(f"Expected constant in DATA statement")
        
        while self.match(TokenType.COMMA):
            self.advance()
            if self.match(TokenType.INTEGER):
                constants.append(self.current_token.value)
                self.advance()
            elif self.match(TokenType.REAL):
                constants.append(self.current_token.value)
                self.advance()
            elif self.match(TokenType.STRING):
                constants.append(self.current_token.value)
                self.advance()
            else:
                raise BasicError(f"Expected constant after comma in list")
        
        return constants
    
    def parse_expression_list(self) -> List[ASTNode]:
        """Parse comma-separated list of expressions"""
        exprs = []
        exprs.append(self.parse_expression())
        
        while self.match(TokenType.COMMA):
            self.advance()
            exprs.append(self.parse_expression())
        
        return exprs
    
    # Expression parsing following the grammar's precedence
    
    def parse_expression(self) -> ASTNode:
        """<Expression> ::= <And Exp> OR <Expression> | <And Exp>"""
        left = self.parse_and_exp()
        
        if self.match(TokenType.OR):
            self.advance()
            right = self.parse_expression()
            return BinaryOpNode(TokenType.OR, left, right)
        
        return left
    
    def parse_and_exp(self) -> ASTNode:
        """<And Exp> ::= <Not Exp> AND <And Exp> | <Not Exp>"""
        left = self.parse_not_exp()
        
        if self.match(TokenType.AND):
            self.advance()
            right = self.parse_and_exp()
            return BinaryOpNode(TokenType.AND, left, right)
        
        return left
    
    def parse_not_exp(self) -> ASTNode:
        """<Not Exp> ::= NOT <Compare Exp> | <Compare Exp>"""
        if self.match(TokenType.NOT):
            self.advance()
            operand = self.parse_compare_exp()
            return UnaryOpNode(TokenType.NOT, operand)
        
        return self.parse_compare_exp()
    
    def parse_compare_exp(self) -> ASTNode:
        """<Compare Exp> ::= <Add Exp> ('=' | '<>' | '>' | '>=' | '<' | '<=') <Compare Exp> | <Add Exp>"""
        left = self.parse_add_exp()
        
        if self.match(TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE):
            op = self.current_token.type
            self.advance()
            right = self.parse_compare_exp()
            return BinaryOpNode(op, left, right)
        
        return left
    
    def parse_add_exp(self) -> ASTNode:
        """<Add Exp> ::= <Mult Exp> (('+' | '-') <Mult Exp>)*  (left-associative)"""
        left = self.parse_mult_exp()
        
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.current_token.type
            self.advance()
            right = self.parse_mult_exp()
            left = BinaryOpNode(op, left, right)
        
        return left
    
    def parse_mult_exp(self) -> ASTNode:
        """<Mult Exp> ::= <Negate Exp> (('*' | '/') <Negate Exp>)*  (left-associative)"""
        left = self.parse_negate_exp()
        
        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE):
            op = self.current_token.type
            self.advance()
            right = self.parse_negate_exp()
            left = BinaryOpNode(op, left, right)
        
        return left
    
    def parse_negate_exp(self) -> ASTNode:
        """<Negate Exp> ::= '-' <Power Exp> | <Power Exp>"""
        if self.match(TokenType.MINUS):
            self.advance()
            operand = self.parse_power_exp()
            return UnaryOpNode(TokenType.MINUS, operand)
        
        return self.parse_power_exp()
    
    def parse_power_exp(self) -> ASTNode:
        """<Power Exp> ::= <Sub Exp> '^' <Power Exp> | <Sub Exp>"""
        left = self.parse_sub_exp()
        
        # Note: Right-associative (unlike other binary ops)
        if self.match(TokenType.POWER):
            self.advance()
            right = self.parse_power_exp()
            return BinaryOpNode(TokenType.POWER, left, right)
        
        return left
    
    def parse_sub_exp(self) -> ASTNode:
        """<Sub Exp> ::= '(' <Expression> ')' | <Value>"""
        if self.match(TokenType.LPAREN):
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        
        return self.parse_value()
    
    def parse_value(self) -> ASTNode:
        """<Value> ::= ID | function_call | constant"""
        
        # Constants
        if self.match(TokenType.INTEGER):
            value = self.current_token.value
            self.advance()
            return NumberNode(value)
        
        if self.match(TokenType.REAL):
            value = self.current_token.value
            self.advance()
            return NumberNode(value)
        
        if self.match(TokenType.STRING):
            value = self.current_token.value
            self.advance()
            return StringNode(value)
        
        # Built-in functions
        func_tokens = [
            TokenType.ABS, TokenType.ASC, TokenType.ATN, TokenType.CHR,
            TokenType.COS, TokenType.EXP, TokenType.INT, TokenType.LEFT,
            TokenType.LEN, TokenType.MID, TokenType.RIGHT, TokenType.RND,
            TokenType.SGN, TokenType.SIN, TokenType.SQR, TokenType.STR,
            TokenType.TAN, TokenType.VAL
        ]
        
        if self.match(*func_tokens):
            func_type = self.current_token.type
            self.advance()
            self.expect(TokenType.LPAREN)
            args = self.parse_expression_list()
            self.expect(TokenType.RPAREN)
            return FunctionCallNode(func_type, args)
        
        # User-defined functions (FN name(...))
        # In C64 BASIC, FN is separate from the function name
        if self.match(TokenType.ID) and self.current_token.value == 'FN':
            self.advance()
            # Read the function name
            if not self.match(TokenType.ID):
                raise BasicError(f"Expected function name after FN at line {self.current_token.line}")
            func_name = 'FN' + self.current_token.value
            self.advance()
            self.expect(TokenType.LPAREN)
            arg = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return FunctionCallNode(TokenType.FUNCTION_ID, [arg], func_name)
        
        # Variable or array access
        if self.match(TokenType.ID):
            var_name = self.current_token.value
            self.advance()
            
            # Check for array subscript
            if self.match(TokenType.LPAREN):
                self.advance()
                indices = self.parse_expression_list()
                self.expect(TokenType.RPAREN)
                return VariableNode(var_name, indices)
            
            return VariableNode(var_name, None)
        
        raise BasicError(f"Unexpected token in expression: {self.current_token.type} at line {self.current_token.line}")


class Interpreter:
    """Execute parsed BASIC program"""

    # A real C64 has ~38 KB of BASIC RAM. 1 000 000 elements is ~25× that physical
    # limit — ample for any authentic program while preventing memory exhaustion from
    # user-controlled DIM dimensions.
    MAX_ARRAY_ELEMENTS = 1_000_000

    def __init__(self, program: Dict[int, List[ASTNode]], timeout: float = 5.0):
        self.program = program
        self.timeout = timeout
        self.start_time: Optional[float] = None
        
        self.line_order = sorted(program.keys())
        self.pc = 0  # Program counter (index into line_order)
        
        self.variables: Dict[str, Any] = {}
        self.arrays: Dict[str, List] = {}
        self.output: List[str] = []
        
        # INPUT data
        self.input_data: List[str] = []
        self.input_index = 0
        
        # DATA/READ support
        self.data_items: List[Any] = []
        self.data_pointer = 0
        
        # FOR loop stack
        self.for_stack: List[Dict] = []
        
        # GOSUB/RETURN stack
        self.return_stack: List[int] = []
        
        # User-defined functions
        self.user_functions: Dict[str, Tuple[List[str], ASTNode]] = {}
    
    def set_input(self, input_string: str):
        """Set input data for INPUT statements"""
        self.input_data = [item.strip().strip('"') for item in input_string.split(',')]
        self.input_index = 0
    
    def get_output(self) -> str:
        """Get accumulated output"""
        return ''.join(self.output)
    
    def _check_timeout(self):
        """Check if execution has exceeded timeout"""
        if self.start_time and time.time() - self.start_time > self.timeout:
            raise BasicTimeout(f"Program execution exceeded {self.timeout} seconds")
    
    def run(self) -> str:
        """Execute the program"""
        self.start_time = time.time()
        self.output = []
        self.pc = 0
        
        # Collect all DATA statements first
        self._collect_data()
        
        # Execute program
        while self.pc < len(self.line_order):
            self._check_timeout()
            
            line_num = self.line_order[self.pc]
            statements = self.program[line_num]
            
            pc_changed = False  # Track if PC was changed by GOTO/GOSUB
            
            for stmt in statements:
                try:
                    result = self.execute_statement(stmt)
                    
                    # Handle control flow
                    if result == 'END' or result == 'STOP':
                        return self.get_output()
                    elif isinstance(result, tuple) and result[0] == 'GOTO':
                        # Jump to line number
                        target_line = result[1]
                        if target_line in self.line_order:
                            self.pc = self.line_order.index(target_line)
                            pc_changed = True
                        else:
                            raise BasicError(f"Line {target_line} not found")
                        break  # Skip remaining statements on this line
                    elif isinstance(result, tuple) and result[0] == 'NEXT_LOOP':
                        # NEXT jumping back to FOR - PC already set, just break and let it increment
                        break
                    elif isinstance(result, tuple) and result[0] == 'RETURN':
                        if not self.return_stack:
                            raise BasicError("RETURN without GOSUB")
                        self.pc = self.return_stack.pop()
                        pc_changed = True
                        break
                
                except BasicError as e:
                    raise BasicError(f"Line {line_num}: {e}")
                except Exception as e:
                    raise BasicError(f"Line {line_num}: {type(e).__name__}: {e}")
            
            # Only increment PC if it wasn't changed by a control flow statement
            if not pc_changed:
                self.pc += 1
        
        return self.get_output()
    
    def _collect_data(self):
        """Collect all DATA statements into data_items list"""
        self.data_items = []
        for line_num in self.line_order:
            for stmt in self.program[line_num]:
                if isinstance(stmt, DataNode):
                    self.data_items.extend(stmt.values)
    
    def execute_statement(self, stmt: ASTNode) -> Optional[Any]:
        """Execute a statement node"""
        
        if isinstance(stmt, RemNode):
            return None
        
        elif isinstance(stmt, DefNode):
            # Store user-defined function
            self.user_functions[stmt.func_name] = (stmt.param, stmt.expression)
            return None
        
        elif isinstance(stmt, AssignmentNode):
            value = self.eval_expression(stmt.expression)
            
            if stmt.indices is None:
                # Simple variable
                # Apply type conversion based on suffix
                if stmt.var_name.endswith('%'):
                    value = int(value)
                elif stmt.var_name.endswith('$'):
                    value = str(value)
                self.variables[stmt.var_name] = value
            else:
                # Array element
                indices = [int(self.eval_expression(idx)) for idx in stmt.indices]
                if stmt.var_name not in self.arrays:
                    raise BasicError(f"Array {stmt.var_name} not declared")
                
                # Apply type conversion
                if stmt.var_name.endswith('%'):
                    value = int(value)
                elif stmt.var_name.endswith('$'):
                    value = str(value)
                
                # Set array element
                arr = self.arrays[stmt.var_name]
                for idx in indices[:-1]:
                    arr = arr[idx]
                arr[indices[-1]] = value
        
        elif isinstance(stmt, PrintNode):
            for expr, sep in stmt.items:
                value = self.eval_expression(expr)
                
                # Format numbers with leading/trailing space
                if isinstance(value, (int, float)):
                    formatted = str(value)
                    if value >= 0:
                        formatted = ' ' + formatted
                    formatted = formatted + ' '
                    self.output.append(formatted)
                else:
                    self.output.append(str(value))
            
            # Add newline unless trailing separator
            if stmt.trailing_sep is None:
                self.output.append('\n')
        
        elif isinstance(stmt, InputNode):
            for var_name in stmt.var_names:
                if self.input_index >= len(self.input_data):
                    raise BasicError(f"Not enough input data for INPUT {var_name}")
                
                value = self.input_data[self.input_index]
                self.input_index += 1
                
                # Convert based on type
                if var_name.endswith('$'):
                    self.variables[var_name] = str(value)
                elif var_name.endswith('%'):
                    self.variables[var_name] = int(float(value))
                else:
                    self.variables[var_name] = float(value)
        
        elif isinstance(stmt, IfNode):
            condition = self.eval_expression(stmt.condition)
            # C64 BASIC: true is -1, false is 0
            if condition != 0:
                if isinstance(stmt.then_clause, int):
                    return ('GOTO', stmt.then_clause)
                else:
                    # Execute statements in then clause
                    for s in stmt.then_clause:
                        result = self.execute_statement(s)
                        if result:
                            return result
        
        elif isinstance(stmt, ForNode):
            start_val = self.eval_expression(stmt.start)
            end_val = self.eval_expression(stmt.end)
            step_val = 1
            if stmt.step:
                step_val = self.eval_expression(stmt.step)
            
            # Initialize loop variable
            if stmt.var_name.endswith('%'):
                self.variables[stmt.var_name] = int(start_val)
            else:
                self.variables[stmt.var_name] = start_val
            
            # Push loop info onto stack
            # Store current PC (the FOR line) - NEXT will jump back here and continue to next line
            self.for_stack.append({
                'var': stmt.var_name,
                'end': end_val,
                'step': step_val,
                'line': self.pc,
                'for_statement': True  # Flag to indicate we should skip FOR re-execution
            })
        
        elif isinstance(stmt, NextNode):
            if not self.for_stack:
                raise BasicError("NEXT without FOR")
            
            loop = self.for_stack[-1]
            
            # Increment loop variable
            current = self.variables[loop['var']]
            new_val = current + loop['step']
            
            if loop['var'].endswith('%'):
                self.variables[loop['var']] = int(new_val)
            else:
                self.variables[loop['var']] = new_val
            
            # Check if loop should continue
            if loop['step'] > 0:
                done = new_val > loop['end']
            else:
                done = new_val < loop['end']
            
            if not done:
                # Jump back to FOR line - set PC but DON'T prevent increment
                # This allows execution to continue from the line after FOR
                self.pc = loop['line']
                return ('NEXT_LOOP',)  # Signal to break but still increment PC
            else:
                # Exit loop
                self.for_stack.pop()
        
        elif isinstance(stmt, GotoNode):
            target = int(self.eval_expression(stmt.target))
            return ('GOTO', target)
        
        elif isinstance(stmt, GosubNode):
            target = int(self.eval_expression(stmt.target))
            # Push return address (next line after GOSUB)
            self.return_stack.append(self.pc + 1)
            return ('GOTO', target)
        
        elif isinstance(stmt, ReturnNode):
            return ('RETURN',)
        
        elif isinstance(stmt, DimNode):
            # Evaluate dimension expressions.
            # +1 because BASIC is 0-indexed but DIM specifies max index (DIM A(10) → indices 0..10).
            dims = [int(self.eval_expression(d)) + 1 for d in stmt.dimensions]

            # Guard against memory exhaustion from user-controlled dimension values.
            total_elements = 1
            for d in dims:
                total_elements *= d
            if total_elements > self.MAX_ARRAY_ELEMENTS:
                raise BasicError(f"Array too large ({total_elements} elements; maximum is {self.MAX_ARRAY_ELEMENTS})")

            arr = self._create_array(dims)
            self.arrays[stmt.var_name] = arr
        
        elif isinstance(stmt, ReadNode):
            for var_name in stmt.var_names:
                if self.data_pointer >= len(self.data_items):
                    raise BasicError("Out of DATA")
                
                value = self.data_items[self.data_pointer]
                self.data_pointer += 1
                
                # Convert based on type
                if var_name.endswith('$'):
                    self.variables[var_name] = str(value)
                elif var_name.endswith('%'):
                    self.variables[var_name] = int(float(value))
                else:
                    self.variables[var_name] = float(value)
        
        elif isinstance(stmt, RestoreNode):
            self.data_pointer = 0
        
        elif isinstance(stmt, EndNode):
            return 'END'
        
        elif isinstance(stmt, StopNode):
            return 'STOP'
        
        elif isinstance(stmt, DataNode):
            # DATA is handled in _collect_data
            pass
        
        return None
    
    def _create_array(self, dims: List[int]) -> List:
        """Create multi-dimensional array"""
        if len(dims) == 1:
            return [0] * dims[0]
        else:
            return [self._create_array(dims[1:]) for _ in range(dims[0])]
    
    def eval_expression(self, node: ASTNode) -> Any:
        """Evaluate an expression node"""
        
        if isinstance(node, NumberNode):
            return node.value
        
        elif isinstance(node, StringNode):
            return node.value
        
        elif isinstance(node, VariableNode):
            # Special system variables
            if node.name == 'TI' and node.indices is None:
                # TI returns jiffies (1/60th second) since start
                if self.start_time:
                    elapsed = time.time() - self.start_time
                    jiffies = int(elapsed * 60)
                    return jiffies
                return 0
            
            if node.indices is None:
                # Simple variable
                if node.name in self.variables:
                    return self.variables[node.name]
                # Undefined variables default to 0 or ""
                if node.name.endswith('$'):
                    return ""
                return 0
            else:
                # Array access
                if node.name not in self.arrays:
                    raise BasicError(f"Array {node.name} not declared")
                
                indices = [int(self.eval_expression(idx)) for idx in node.indices]
                arr = self.arrays[node.name]
                for idx in indices:
                    arr = arr[idx]
                return arr
        
        elif isinstance(node, BinaryOpNode):
            left = self.eval_expression(node.left)
            right = self.eval_expression(node.right)
            
            if node.op == TokenType.PLUS:
                return left + right
            elif node.op == TokenType.MINUS:
                return left - right
            elif node.op == TokenType.MULTIPLY:
                return left * right
            elif node.op == TokenType.DIVIDE:
                return left / right
            elif node.op == TokenType.POWER:
                return left ** right
            elif node.op == TokenType.EQ:
                return -1 if left == right else 0
            elif node.op == TokenType.NE:
                return -1 if left != right else 0
            elif node.op == TokenType.LT:
                return -1 if left < right else 0
            elif node.op == TokenType.LE:
                return -1 if left <= right else 0
            elif node.op == TokenType.GT:
                return -1 if left > right else 0
            elif node.op == TokenType.GE:
                return -1 if left >= right else 0
            elif node.op == TokenType.AND:
                return -1 if (left != 0 and right != 0) else 0
            elif node.op == TokenType.OR:
                return -1 if (left != 0 or right != 0) else 0
        
        elif isinstance(node, UnaryOpNode):
            operand = self.eval_expression(node.operand)
            
            if node.op == TokenType.MINUS:
                return -operand
            elif node.op == TokenType.NOT:
                return -1 if operand == 0 else 0
        
        elif isinstance(node, FunctionCallNode):
            return self.call_function(node.func_type, node.args, node.func_name)
        
        raise BasicError(f"Cannot evaluate node type: {type(node)}")
    
    def call_function(self, func_type: TokenType, args: List[ASTNode], func_name: Optional[str] = None) -> Any:
        """Call a built-in or user-defined function"""
        
        # User-defined functions (FN...)
        if func_type == TokenType.FUNCTION_ID and func_name:
            if func_name not in self.user_functions:
                raise BasicError(f"Undefined function: {func_name}")
            
            param_name, expression = self.user_functions[func_name]
            
            # Evaluate the argument
            arg_value = self.eval_expression(args[0])
            
            # Save current value of parameter variable (if it exists)
            saved_value = self.variables.get(param_name)
            
            # Set parameter to argument value
            self.variables[param_name] = arg_value
            
            # Evaluate function expression
            result = self.eval_expression(expression)
            
            # Restore original parameter value
            if saved_value is not None:
                self.variables[param_name] = saved_value
            else:
                self.variables.pop(param_name, None)
            
            return result
        
        if func_type == TokenType.ABS:
            return abs(self.eval_expression(args[0]))
        
        elif func_type == TokenType.INT:
            return int(self.eval_expression(args[0]))
        
        elif func_type == TokenType.SGN:
            val = self.eval_expression(args[0])
            if val > 0:
                return 1
            elif val < 0:
                return -1
            return 0
        
        elif func_type == TokenType.SQR:
            return math.sqrt(self.eval_expression(args[0]))
        
        elif func_type == TokenType.SIN:
            return math.sin(self.eval_expression(args[0]))
        
        elif func_type == TokenType.COS:
            return math.cos(self.eval_expression(args[0]))
        
        elif func_type == TokenType.TAN:
            return math.tan(self.eval_expression(args[0]))
        
        elif func_type == TokenType.ATN:
            return math.atan(self.eval_expression(args[0]))
        
        elif func_type == TokenType.EXP:
            return math.exp(self.eval_expression(args[0]))
        
        elif func_type == TokenType.RND:
            val = self.eval_expression(args[0])
            if val < 0:
                random.seed(int(val))
            return random.random()
        
        elif func_type == TokenType.LEN:
            s = str(self.eval_expression(args[0]))
            return len(s)
        
        elif func_type == TokenType.ASC:
            s = str(self.eval_expression(args[0]))
            return _petscii_asc(s) if s else 0
        
        elif func_type == TokenType.VAL:
            s = str(self.eval_expression(args[0])).strip()
            try:
                if '.' in s:
                    return float(s)
                return int(s)
            except ValueError:
                return 0
        
        elif func_type == TokenType.CHR:
            code = int(self.eval_expression(args[0]))
            return _petscii_chr(code)
        
        elif func_type == TokenType.STR:
            val = self.eval_expression(args[0])
            result = str(val)
            if val >= 0 and not result.startswith(' '):
                result = ' ' + result
            return result
        
        elif func_type == TokenType.LEFT:
            s = str(self.eval_expression(args[0]))
            n = int(self.eval_expression(args[1]))
            return s[:n]
        
        elif func_type == TokenType.RIGHT:
            s = str(self.eval_expression(args[0]))
            n = int(self.eval_expression(args[1]))
            return s[-n:] if n > 0 else ""
        
        elif func_type == TokenType.MID:
            s = str(self.eval_expression(args[0]))
            start = int(self.eval_expression(args[1])) - 1  # 1-indexed
            if len(args) == 3:
                length = int(self.eval_expression(args[2]))
                return s[start:start+length]
            return s[start:]
        
        raise BasicError(f"Unknown function: {func_type}")


class BasicInterpreter:
    """Main interpreter class"""
    
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.program = None
        self.interpreter = None
    
    def load_program(self, source: str):
        """Load and parse a BASIC program"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        parser = Parser(tokens)
        self.program = parser.parse_program()
        
        self.interpreter = Interpreter(self.program, self.timeout)
    
    def set_input(self, input_string: str):
        """Set input data for INPUT statements"""
        if self.interpreter:
            self.interpreter.set_input(input_string)
    
    def run(self) -> str:
        """Execute the program"""
        if not self.interpreter:
            raise BasicError("No program loaded")
        return self.interpreter.run()
    
    @property
    def variables(self):
        """Access interpreter variables"""
        return self.interpreter.variables if self.interpreter else {}
    
    @property
    def arrays(self):
        """Access interpreter arrays"""
        return self.interpreter.arrays if self.interpreter else {}


def run_basic_program(source: str, input_data: str = "", timeout: float = 5.0) -> str:
    """Convenience function to run a BASIC program"""
    interpreter = BasicInterpreter(timeout=timeout)
    interpreter.load_program(source)
    if input_data:
        interpreter.set_input(input_data)
    return interpreter.run()
