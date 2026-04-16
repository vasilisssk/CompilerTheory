from src.ast import nodes as ast
from src.semantic.errors import SemanticError
from typing import Dict, Optional, Any


class SymbolTable:
    def __init__(self, parent: Optional['SymbolTable'] = None):
        self.parent = parent
        self.symbols: Dict[str, str] = {}

    def add(self, name: str, type_name: str):
        if name in self.symbols:
            raise SemanticError(f"Переменная '{name}' уже объявлена в этой области")
        self.symbols[name] = type_name

    def lookup(self, name: str) -> Optional[str]:
        if name in self.symbols:
            return self.symbols[name]
        return self.parent.lookup(name) if self.parent else None


VALID_TYPES = {"integer", "boolean", "char"}
BUILTIN_PROCS = {"write", "writeln", "read", "readln"}


class SemanticAnalyzer:
    def __init__(self):
        self.scopes = [SymbolTable()]
        self.loop_depth = 0

    def _current_scope(self) -> SymbolTable:
        return self.scopes[-1]

    def _enter_scope(self):
        self.scopes.append(SymbolTable(self._current_scope()))

    def _exit_scope(self):
        self.scopes.pop()

    def _annotate(self, node: ast.ASTNode, type_name: str):
        node.inferred_type = type_name

    def visit(self, node: Any):
        method = getattr(self, f"visit_{type(node).__name__}", self.generic_visit)
        return method(node)

    def generic_visit(self, node: Any):
        for child in getattr(node, "__dict__", {}).values():
            if isinstance(child, ast.ASTNode):
                self.visit(child)
            elif isinstance(child, list):
                for item in child:
                    if isinstance(item, ast.ASTNode):
                        self.visit(item)

    def visit_Program(self, node: ast.Program):
        self.visit(node.block)

    def visit_Block(self, node: ast.Block):
        self._enter_scope()
        for decl in node.var_decls:
            self.visit(decl)
        self.visit(node.body)
        self._exit_scope()

    def visit_VarDecl(self, node: ast.VarDecl):
        if node.type_name not in VALID_TYPES:
            raise SemanticError(f"Неизвестный тип '{node.type_name}'", node)
        self._current_scope().add(node.ident.name, node.type_name)

    def visit_CompoundStmt(self, node: ast.CompoundStmt):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_Assign(self, node: ast.Assign):
        lhs_type = self._current_scope().lookup(node.ident.name)
        if lhs_type is None:
            raise SemanticError(f"Необъявленная переменная '{node.ident.name}'", node)

        rhs_type = self.visit(node.expr)
        if lhs_type != rhs_type:
            raise SemanticError(f"Несоответствие типов: нельзя присвоить '{rhs_type}' переменной типа '{lhs_type}'",
                                node)
        self._annotate(node, lhs_type)
        return lhs_type

    def visit_If(self, node: ast.If):
        cond_type = self.visit(node.cond)
        if cond_type != "boolean":
            raise SemanticError("Условие if должно быть типа boolean", node)
        self.visit(node.then_branch)
        if node.else_branch:
            self.visit(node.else_branch)

    def visit_While(self, node: ast.While):
        cond_type = self.visit(node.cond)
        if cond_type != "boolean":
            raise SemanticError("Условие while должно быть типа boolean", node)
        self.loop_depth += 1
        self.visit(node.body)
        self.loop_depth -= 1

    def visit_For(self, node: ast.For):
        start_type = self.visit(node.start)
        end_type = self.visit(node.end)
        if start_type != "integer" or end_type != "integer":
            raise SemanticError("Границы цикла for должны быть integer", node)

        # ✅ ИСПРАВЛЕНИЕ: проверяем существующую переменную, а не создаём новую
        var_type = self._current_scope().lookup(node.ident.name)
        if var_type is None:
            raise SemanticError(f"Переменная цикла '{node.ident.name}' не объявлена", node)
        if var_type != "integer":
            raise SemanticError(f"Переменная цикла '{node.ident.name}' должна иметь тип integer", node)

        self.loop_depth += 1
        self.visit(node.body)
        self.loop_depth -= 1

    def visit_Break(self, node: ast.Break):
        if self.loop_depth == 0:
            raise SemanticError("'break' вне цикла", node)

    def visit_Continue(self, node: ast.Continue):
        if self.loop_depth == 0:
            raise SemanticError("'continue' вне цикла", node)

    def visit_BinOp(self, node: ast.BinOp):
        l_type = self.visit(node.left)
        r_type = self.visit(node.right)
        op = node.op.value

        if op in ("+", "-", "*") and l_type == r_type == "integer":
            self._annotate(node, "integer")
            return "integer"
        if op == "/" and l_type == r_type == "integer":
            self._annotate(node, "real")
            return "real"
        if op in ("div", "mod") and l_type == r_type == "integer":
            self._annotate(node, "integer")
            return "integer"
        if op in ("and", "or") and l_type == r_type == "boolean":
            self._annotate(node, "boolean")
            return "boolean"
        if op in ("=", "<>", "<", "<=", ">", ">=") and l_type == r_type:
            self._annotate(node, "boolean")
            return "boolean"

        raise SemanticError(f"Оператор '{op}' не применим к типам '{l_type}' и '{r_type}'", node)

    def visit_UnOp(self, node: ast.UnOp):
        inner_type = self.visit(node.expr)
        if node.op.value == "not":
            if inner_type != "boolean":
                raise SemanticError("'not' требует boolean", node)
            self._annotate(node, "boolean")
            return "boolean"
        if node.op.value in ("+", "-"):
            if inner_type not in ("integer", "real"):
                raise SemanticError(f"Унарный '{node.op.value}' требует числовой тип", node)
            self._annotate(node, inner_type)
            return inner_type
        raise SemanticError(f"Неизвестный унарный оператор", node)

    def visit_Ident(self, node: ast.Ident):
        t = self._current_scope().lookup(node.name)
        if t is None:
            raise SemanticError(f"Необъявленная переменная '{node.name}'", node)
        self._annotate(node, t)
        return t

    def visit_Literal(self, node: ast.Literal):
        if isinstance(node.value, bool):
            self._annotate(node, "boolean")
            return "boolean"
        if isinstance(node.value, int):
            self._annotate(node, "integer")
            return "integer"
        if isinstance(node.value, str) and len(node.value) == 1:
            self._annotate(node, "char")
            return "char"
        raise SemanticError("Неизвестный тип литерала", node)

    def visit_Call(self, node: ast.Call):
        if node.func.name not in BUILTIN_PROCS:
            raise SemanticError(f"Неизвестная процедура '{node.func.name}'", node)
        for arg in node.args:
            self.visit(arg)
        self._annotate(node, "void")
        return "void"