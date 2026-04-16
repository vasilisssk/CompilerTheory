from src.ast import nodes as ast
from typing import List

class PythonCodeGenerator:
    def __init__(self):
        self.output: List[str] = []
        self.indent = 0

    def _push(self, line: str):
        self.output.append("    " * self.indent + line)

    def generate(self, node: ast.Program) -> str:
        self.visit(node)
        return "\n".join(self.output)

    def visit(self, node: ast.ASTNode):
        method = getattr(self, f"visit_{type(node).__name__}", self.generic_visit)
        method(node)

    def generic_visit(self, node: ast.ASTNode):
        for child in getattr(node, "__dict__", {}).values():
            if isinstance(child, ast.ASTNode):
                self.visit(child)
            elif isinstance(child, list):
                for item in child:
                    if isinstance(item, ast.ASTNode):
                        self.visit(item)

    def visit_Program(self, node: ast.Program):
        self._push("# Generated Pascal -> Python")
        self.visit(node.block)

    def visit_Block(self, node: ast.Block):
        for decl in node.var_decls:
            self.visit(decl)
        self.visit(node.body)

    def visit_VarDecl(self, node: ast.VarDecl):
        self._push(f"# var {node.ident.name}: {node.type_name}")

    def visit_CompoundStmt(self, node: ast.CompoundStmt):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_Assign(self, node: ast.Assign):
        self._push(f"{node.ident.name} = {self._expr(node.expr)}")

    def visit_If(self, node: ast.If):
        self._push(f"if {self._expr(node.cond)}:")
        self.indent += 1
        self.visit(node.then_branch)
        self.indent -= 1
        if node.else_branch:
            self._push("else:")
            self.indent += 1
            self.visit(node.else_branch)
            self.indent -= 1

    def visit_While(self, node: ast.While):
        self._push(f"while {self._expr(node.cond)}:")
        self.indent += 1
        self.visit(node.body)
        self.indent -= 1

    def visit_For(self, node: ast.For):
        start = self._expr(node.start)
        end = self._expr(node.end)
        if node.direction == "to":
            self._push(f"for {node.ident.name} in range(int({start}), int({end}) + 1):")
        else:
            self._push(f"for {node.ident.name} in range(int({start}), int({end}) - 1, -1):")
        self.indent += 1
        self.visit(node.body)
        self.indent -= 1

    def visit_Break(self, node: ast.Break):
        self._push("break")

    def visit_Continue(self, node: ast.Continue):
        self._push("continue")

    def visit_Call(self, node: ast.Call):
        args = ", ".join(self._expr(a) for a in node.args)
        if node.func.name == "write":
            self._push(f"print({args}, end='')")
        elif node.func.name == "writeln":
            self._push(f"print({args})")
        elif node.func.name == "read":
            self._push(f"input()  # read placeholder")

    def _expr(self, node: ast.Expr) -> str:
        if isinstance(node, ast.Literal):
            if isinstance(node.value, bool):
                return "True" if node.value else "False"
            return str(node.value)
        if isinstance(node, ast.Ident):
            return node.name
        if isinstance(node, ast.BinOp):
            l, r = self._expr(node.left), self._expr(node.right)
            op_map = {"div": "//", "mod": "%", "and": "and", "or": "or"}
            op = op_map.get(node.op.value, node.op.value)
            return f"({l} {op} {r})"
        if isinstance(node, ast.UnOp):
            inner = self._expr(node.expr)
            if node.op.value == "not":
                return f"(not {inner})"
            return f"({node.op.value}{inner})"
        return "?"