from src.pascal.parser import PascalParser
from src.ast.builder import dump_ast


def main():
    text = '''program test;
                var
                  x, y: integer;
                  b1, b2: boolean;
                  ch: char;
                begin
                  x := 2 + 3 * 4;
                  y := x div 2 - 5 mod 3;
                  b1 := true;
                  b2 := false;
                  ch := 'A';

                  if x > 10 then
                    x := x - 1
                  else
                    x := x + 1;

                  while x > 0 do
                    x := x - 1;

                  for y := 1 to 5 do
                  begin
                    if y = 3 then continue;
                    if y = 2 then break;
                    x := x + y;
                  end;

                  for y := 5 downto 1 do
                    x := x - y;

                  if not b1 or (b1 and b2) then
                    b1 := false
                  else
                    b1 := true;

                  write(x);
                  writeln(x);
                  read(ch)
                end.
                '''

    parser = PascalParser(text)
    program = parser.parse_program()

    print(dump_ast(program))


if __name__ == "__main__":
    main()
