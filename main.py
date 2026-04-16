from src.pascal.parser import PascalParser, PascalParserError
from src.ast.builder import dump_ast
import sys
from pathlib import Path
from src.semantic.analyzer import SemanticAnalyzer
from src.semantic.errors import SemanticError
from src.codegen.python_gen import PythonCodeGenerator

sys.path.insert(0, str(Path(__file__).parent.parent))

EXAMPLE_FILES = [
    "minimal.pasc",
    "if_example.pasc",
    "while_example.pasc",
    "for_example.pasc",
    "logic_example.pasc",
    "read_example.pasc",
    "syntax_error.pasc",
    "semantic_error.pasc"
]

def process_file(file_path: Path) -> bool:
    """Обрабатывает один файл: парсинг, семантический анализ, генерация кода"""
    print(f"--- Processing: {file_path.name} ---")

    try:
        text = file_path.read_text(encoding='utf-8')
        parser = PascalParser(text)
        program = parser.parse_program()

        # Семантический анализ
        analyzer = SemanticAnalyzer()
        analyzer.visit(program)

        # Дерево
        print(dump_ast(program))

        # Генерация Python-кода
        generator = PythonCodeGenerator()
        python_code = generator.generate(program)

        print("[SUCCESS] Semantic analysis passed\n")
        print("- Generated Python code -")
        print(python_code + "\n")
        return True

    except PascalParserError as e:
        print(f"[SYNTAX ERROR] {e}\n")
        return False
    except SemanticError as e:
        print(f"[SEMANTIC ERROR] {e.message}")
        if e.node:
            # Если узел имеет информацию о позиции (можно расширить)
            print(f"  at node: {type(e.node).__name__}\n")
        return False
    except Exception as e:
        print(f"[UNEXPECTED ERROR] {type(e).__name__}: {e}\n")
        return False

def main():
    base_dir = Path(__file__).parent
    examples_dir = base_dir / "src" / "examples"

    if not examples_dir.exists():
        print(f"Error: examples directory not found at {examples_dir}")
        return

    success_count = 0
    for filename in EXAMPLE_FILES:
        file_path = examples_dir / filename
        if not file_path.exists():
            print(f"Warning: {filename} not found, skipping")
            continue
        if process_file(file_path):
            success_count += 1

    print(f"\nSummary: {success_count} / {len(EXAMPLE_FILES)} files processed successfully")

if __name__ == "__main__":
    main()