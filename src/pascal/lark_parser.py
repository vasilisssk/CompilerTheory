from __future__ import annotations
from pathlib import Path
from lark import Lark, Transformer, UnexpectedInput

from src.ast import nodes as ast


class PascalParserError(Exception):
    pass


class ASTBuilder(Transformer):
    binary_ops = {
        "bin_or_rule": ast.BinaryOpKind.OR,
        "bin_and_rule": ast.BinaryOpKind.AND,
        "bin_eq_rule": ast.BinaryOpKind.EQ,
        "bin_ne_rule": ast.BinaryOpKind.NE,
        "bin_lt_rule": ast.BinaryOpKind.LT,
        "bin_le_rule": ast.BinaryOpKind.LE,
        "bin_gt_rule": ast.BinaryOpKind.GT,
        "bin_ge_rule": ast.BinaryOpKind.GE,
        "bin_add_rule": ast.BinaryOpKind.ADD,
        "bin_sub_rule": ast.BinaryOpKind.SUB,
        "bin_mul_rule": ast.BinaryOpKind.MUL,
        "bin_float_div_rule": ast.BinaryOpKind.FLOAT_DIV,
        "bin_int_div_rule": ast.BinaryOpKind.INT_DIV,
        "bin_mod_rule": ast.BinaryOpKind.MOD,
    }
    unary_ops = {
        "un_not_rule": ast.UnaryOpKind.NOT,
        "un_plus_rule": ast.UnaryOpKind.PLUS,
        "un_minus_rule": ast.UnaryOpKind.MINUS,
    }

    @staticmethod
    def program_rule(items):
        # items: [IDENT, block]
        return ast.Program(name=str(items[0]), block=items[1])

    @staticmethod
    def block_rule(items):
        # items: [compound_stmt] или [var_section, compound_stmt]
        if len(items) == 1:
            return ast.Block(var_decls=[], body=items[0])
        return ast.Block(var_decls=items[0], body=items[1])

    @staticmethod
    def var_section_rule(items):
        decls = []
        for item in items:
            decls.extend(item)
        return decls

    @staticmethod
    def var_decl_rule(items):
        # items: [ident_list, TYPE_NAME]
        names = items[0]
        type_name = str(items[1])
        return [ast.VarDecl(ident=ast.Ident(name=name), type_name=type_name) for name in names]

    @staticmethod
    def ident_list_rule(items):
        return [str(item) for item in items]

    @staticmethod
    def compound_stmt_rule(items):
        # items: [stmt_list?] – может быть пустым
        if not items:
            return ast.CompoundStmt(statements=[])
        return items[0]

    @staticmethod
    def stmt_list_rule(items):
        return ast.CompoundStmt(statements=items)

    def if_stmt_rule(self, items):
        # items: [expr, then_stmt] или [expr, then_stmt, else_stmt]
        cond = items[0]
        then_branch = self._to_compound(items[1])
        else_branch = self._to_compound(items[2]) if len(items) == 3 else None
        return ast.If(cond=cond, then_branch=then_branch, else_branch=else_branch)

    def while_stmt_rule(self, items):
        # items: [expr, stmt]
        return ast.While(cond=items[0], body=self._to_compound(items[1]))

    def for_stmt_rule(self, items):
        # items: [IDENT, start_expr, FOR_DIR, end_expr, body_stmt]
        ident_name = str(items[0])
        start_expr = items[1]
        direction = str(items[2])  # "to" или "downto"
        end_expr = items[3]
        body_stmt = self._to_compound(items[4])
        return ast.For(
            ident=ast.Ident(name=ident_name),
            start=start_expr,
            direction=direction,
            end=end_expr,
            body=body_stmt,
        )

    @staticmethod
    def break_stmt_rule(_):
        return ast.Break()

    @staticmethod
    def continue_stmt_rule(_):
        return ast.Continue()

    @staticmethod
    def assign_stmt_rule(items):
        # items: [IDENT, expr]
        return ast.Assign(ident=ast.Ident(name=str(items[0])), expr=items[1])

    @staticmethod
    def call_stmt_rule(items):
        return items[0]

    @staticmethod
    def call_rule(items):
        # items: [call_name] или [call_name, arg_list]
        func_name = items[0]
        args = items[1] if len(items) == 2 else []
        return ast.Call(func=ast.Ident(name=func_name), args=args)

    @staticmethod
    def call_name_rule(items):
        return str(items[0])

    @staticmethod
    def arg_list_rule(items):
        return list(items)


    @staticmethod
    def int_lit_rule(items):
        return ast.Literal(value=int(items[0]))

    @staticmethod
    def char_lit_rule(items):
        value = str(items[0])[1:-1]
        return ast.Literal(value=value)

    @staticmethod
    def true_lit_rule(_):
        return ast.Literal(value=True)

    @staticmethod
    def false_lit_rule(_):
        return ast.Literal(value=False)

    @staticmethod
    def ident_rule(items):
        return ast.Ident(name=str(items[0]))

    def __getattr__(self, name):
        if name in self.binary_ops:
            return lambda items: ast.BinOp(left=items[0], op=self.binary_ops[name], right=items[1])
        if name in self.unary_ops:
            return lambda items: ast.UnOp(op=self.unary_ops[name], expr=items[0])
        raise AttributeError(name)

    @staticmethod
    def _to_compound(stmt):
        if isinstance(stmt, ast.CompoundStmt):
            return stmt
        return ast.CompoundStmt(statements=[stmt])


class PascalParser:

    def __init__(self, text: str):
        self.text = text
        grammar_path = Path(__file__).with_name("pascal.lark")
        grammar = grammar_path.read_text(encoding="utf-8")
        self.parser = Lark(grammar, start="program_rule", parser="lalr")

    def parse_program(self) -> ast.Program:
        try:
            tree = self.parser.parse(self.text)
            return ASTBuilder().transform(tree)
        except UnexpectedInput as error:
            raise PascalParserError(str(error)) from error