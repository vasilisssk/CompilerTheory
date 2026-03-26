from enum import Enum, auto
import re
from src.ast import nodes as ast

class PascalParserError(Exception):
    pass

class TokenType(Enum):
    IDENT = auto()
    INT = auto()
    CHAR = auto()

    PLUS = auto()
    MINUS = auto()
    MUL = auto()
    FLOAT_DIV = auto()
    INT_DIV = auto()
    MOD = auto()

    ASSIGN = auto()

    EQ = auto()
    NE = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()

    LPAREN = auto()
    RPAREN = auto()
    SEMI = auto()
    COLON = auto()
    COMMA = auto()
    DOT = auto()

    PROGRAM = auto()
    VAR = auto()
    BEGIN = auto()
    END = auto()

    IF = auto()
    THEN = auto()
    ELSE = auto()

    WHILE = auto()
    DO = auto()

    FOR = auto()
    TO = auto()
    DOWNTO = auto()

    BREAK = auto()
    CONTINUE = auto()

    AND = auto()
    OR = auto()
    NOT = auto()

    TRUE = auto()
    FALSE = auto()

    EOF = auto()


KEYWORDS = {
    "program": TokenType.PROGRAM,
    "var": TokenType.VAR,
    "begin": TokenType.BEGIN,
    "end": TokenType.END,
    "if": TokenType.IF,
    "then": TokenType.THEN,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "do": TokenType.DO,
    "for": TokenType.FOR,
    "to": TokenType.TO,
    "downto": TokenType.DOWNTO,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "div": TokenType.INT_DIV,
    "mod": TokenType.MOD,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
}


class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value


class Lexer:
    def __init__(self, text):
        self.tokens = self.tokenize(text)
        self.pos = 0

    def tokenize(self, text):
        token_spec = [
            ("CHAR", r"'[^']'"),
            ("INT", r"\d+"),
            ("IDENT", r"[a-zA-Z_]\w*"),

            ("ASSIGN", r":="),
            ("LE", r"<="),
            ("GE", r">="),
            ("NE", r"<>"),
            ("LT", r"<"),
            ("GT", r">"),
            ("EQ", r"="),

            ("PLUS", r"\+"),
            ("MINUS", r"-"),
            ("MUL", r"\*"),
            ("FLOAT_DIV", r"/"),

            ("LPAREN", r"\("),
            ("RPAREN", r"\)"),
            ("SEMI", r";"),
            ("COLON", r":"),
            ("COMMA", r","),
            ("DOT", r"\."),

            ("SKIP", r"[ \t\n]+"),
        ]

        tok_regex = "|".join(f"(?P<{n}>{r})" for n, r in token_spec)
        tokens = []

        for m in re.finditer(tok_regex, text):
            kind = m.lastgroup
            value = m.group()

            if kind == "SKIP":
                continue

            if kind == "IDENT":
                token_type = KEYWORDS.get(value.lower(), TokenType.IDENT)
            else:
                token_type = TokenType[kind]

            tokens.append(Token(token_type, value))

        tokens.append(Token(TokenType.EOF, None))
        return tokens

    def peek(self):
        return self.tokens[self.pos]

    def next(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

class PascalParser:

    def __init__(self, text):
        self.lexer = Lexer(text)

    def eat(self, t):
        tok = self.lexer.peek()
        if tok.type != t:
            raise PascalParserError(f"Expected {t}, got {tok.type}")
        return self.lexer.next()

    def parse_program(self):
        self.eat(TokenType.PROGRAM)
        name = self.eat(TokenType.IDENT).value
        self.eat(TokenType.SEMI)

        block = self.parse_block()

        self.eat(TokenType.DOT)
        return ast.Program(name=name, block=block)

    def parse_block(self):
        var_decls = []
        if self.lexer.peek().type == TokenType.VAR:
            self.eat(TokenType.VAR)
            var_decls = self.parse_var_section()

        body = self.parse_compound()
        return ast.Block(var_decls=var_decls, body=body)

    def parse_var_section(self):
        decls = []
        while self.lexer.peek().type == TokenType.IDENT:
            names = self.parse_ident_list()
            self.eat(TokenType.COLON)
            type_name = self.eat(TokenType.IDENT).value
            self.eat(TokenType.SEMI)

            for n in names:
                decls.append(ast.VarDecl(ast.Ident(n), type_name))
        return decls

    def parse_ident_list(self):
        names = [self.eat(TokenType.IDENT).value]
        while self.lexer.peek().type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            names.append(self.eat(TokenType.IDENT).value)
        return names

    def parse_compound(self):
        self.eat(TokenType.BEGIN)
        stmts = self.parse_stmt_list()
        self.eat(TokenType.END)
        return ast.CompoundStmt(stmts)

    def parse_stmt_list(self):
        stmts = [self.parse_stmt()]
        while self.lexer.peek().type == TokenType.SEMI:
            self.eat(TokenType.SEMI)
            stmts.append(self.parse_stmt())
        return stmts

    def parse_stmt(self):
        tok = self.lexer.peek()

        if tok.type == TokenType.BEGIN:
            return self.parse_compound()
        if tok.type == TokenType.IF:
            return self.parse_if()
        if tok.type == TokenType.WHILE:
            return self.parse_while()
        if tok.type == TokenType.FOR:
            return self.parse_for()
        if tok.type == TokenType.BREAK:
            self.eat(TokenType.BREAK)
            return ast.Break()
        if tok.type == TokenType.CONTINUE:
            self.eat(TokenType.CONTINUE)
            return ast.Continue()
        if tok.type == TokenType.IDENT:
            return self.parse_assign_or_call()

        return ast.CompoundStmt([])

    def parse_if(self):
        self.eat(TokenType.IF)
        cond = self.parse_expr()
        self.eat(TokenType.THEN)
        then_b = self.wrap(self.parse_stmt())

        else_b = None
        if self.lexer.peek().type == TokenType.ELSE:
            self.eat(TokenType.ELSE)
            else_b = self.wrap(self.parse_stmt())

        return ast.If(cond, then_b, else_b)

    def parse_while(self):
        self.eat(TokenType.WHILE)
        cond = self.parse_expr()
        self.eat(TokenType.DO)
        return ast.While(cond, self.wrap(self.parse_stmt()))

    def parse_for(self):
        self.eat(TokenType.FOR)
        name = self.eat(TokenType.IDENT).value
        self.eat(TokenType.ASSIGN)

        start = self.parse_expr()

        direction_tok = self.lexer.next()
        direction = direction_tok.value

        end = self.parse_expr()
        self.eat(TokenType.DO)

        body = self.wrap(self.parse_stmt())

        return ast.For(ast.Ident(name), start, direction, end, body)

    def parse_assign_or_call(self):
        name = self.eat(TokenType.IDENT).value

        if self.lexer.peek().type == TokenType.ASSIGN:
            self.eat(TokenType.ASSIGN)
            expr = self.parse_expr()
            return ast.Assign(ast.Ident(name), expr)

        args = []
        if self.lexer.peek().type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            if self.lexer.peek().type != TokenType.RPAREN:
                args.append(self.parse_expr())
                while self.lexer.peek().type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                    args.append(self.parse_expr())
            self.eat(TokenType.RPAREN)

        return ast.Call(ast.Ident(name), args)

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        node = self.parse_and()
        while self.lexer.peek().type == TokenType.OR:
            self.eat(TokenType.OR)
            node = ast.BinOp(ast.BinaryOpKind.OR, node, self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_cmp()
        while self.lexer.peek().type == TokenType.AND:
            self.eat(TokenType.AND)
            node = ast.BinOp(ast.BinaryOpKind.AND, node, self.parse_cmp())
        return node

    def parse_cmp(self):
        node = self.parse_add()
        while self.lexer.peek().type in {
            TokenType.EQ, TokenType.NE,
            TokenType.LT, TokenType.LE,
            TokenType.GT, TokenType.GE,
        }:
            op = self.lexer.next()
            kind = {
                TokenType.EQ: ast.BinaryOpKind.EQ,
                TokenType.NE: ast.BinaryOpKind.NE,
                TokenType.LT: ast.BinaryOpKind.LT,
                TokenType.LE: ast.BinaryOpKind.LE,
                TokenType.GT: ast.BinaryOpKind.GT,
                TokenType.GE: ast.BinaryOpKind.GE,
            }[op.type]
            node = ast.BinOp(kind, node, self.parse_add())
        return node

    def parse_add(self):
        node = self.parse_term()
        while self.lexer.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.lexer.next()
            kind = ast.BinaryOpKind.ADD if op.type == TokenType.PLUS else ast.BinaryOpKind.SUB
            node = ast.BinOp(kind, node, self.parse_term())
        return node

    def parse_term(self):
        node = self.parse_unary()
        while self.lexer.peek().type in (TokenType.MUL, TokenType.FLOAT_DIV,
                                        TokenType.INT_DIV, TokenType.MOD):
            op = self.lexer.next()
            kind = {
                TokenType.MUL: ast.BinaryOpKind.MUL,
                TokenType.FLOAT_DIV: ast.BinaryOpKind.FLOAT_DIV,
                TokenType.INT_DIV: ast.BinaryOpKind.INT_DIV,
                TokenType.MOD: ast.BinaryOpKind.MOD,
            }[op.type]
            node = ast.BinOp(kind, node, self.parse_unary())
        return node

    def parse_unary(self):
        tok = self.lexer.peek()

        if tok.type == TokenType.NOT:
            self.eat(TokenType.NOT)
            return ast.UnOp(ast.UnaryOpKind.NOT, self.parse_unary())

        if tok.type == TokenType.PLUS:
            self.eat(TokenType.PLUS)
            return ast.UnOp(ast.UnaryOpKind.PLUS, self.parse_unary())

        if tok.type == TokenType.MINUS:
            self.eat(TokenType.MINUS)
            return ast.UnOp(ast.UnaryOpKind.MINUS, self.parse_unary())

        return self.parse_factor()

    def parse_factor(self):
        tok = self.lexer.peek()

        if tok.type == TokenType.INT:
            return ast.Literal(int(self.eat(TokenType.INT).value))

        if tok.type == TokenType.CHAR:
            value = self.eat(TokenType.CHAR).value  # <-- ВАЖНО
            return ast.Literal(value[1:-1])

        if tok.type == TokenType.TRUE:
            self.eat(TokenType.TRUE)
            return ast.Literal(True)

        if tok.type == TokenType.FALSE:
            self.eat(TokenType.FALSE)
            return ast.Literal(False)

        if tok.type == TokenType.IDENT:
            return ast.Ident(self.eat(TokenType.IDENT).value)

        if tok.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.parse_expr()
            self.eat(TokenType.RPAREN)
            return node

        raise PascalParserError(f"Unexpected token {tok.type}")

    def wrap(self, stmt):
        if isinstance(stmt, ast.CompoundStmt):
            return stmt
        return ast.CompoundStmt([stmt])