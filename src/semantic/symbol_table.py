from typing import Dict, Optional

class SymbolTable:
    def __init__(self, parent=None):
        self.parent = parent
        self.symbols: Dict[str, str] = {}  # name -> type

    def add(self, name: str, type_name: str) -> bool:
        """Добавить символ. Возвращает False если уже существует."""
        if name in self.symbols:
            return False
        self.symbols[name] = type_name
        return True

    def lookup(self, name: str) -> Optional[str]:
        """Найти тип переменной. Ищет в текущей и родительских областях."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

class SemanticError(Exception):
    """Ошибка семантического анализа"""
    def __init__(self, message: str, line: int = None):
        self.message = message
        self.line = line
        super().__init__(self.message)