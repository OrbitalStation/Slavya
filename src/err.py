from typing import NoReturn
from sys import stderr


def error(file: str, line: int, column: int, code_line: str, description: str) -> NoReturn:
    location = f"At {file}:{line}:{column}"
    print(location + "\n\t" + code_line + "\n" + description, file=stderr)
    exit(1)
