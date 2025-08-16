from rich.console import Console
from rich.text import Text

_console = Console()

def info(msg: str):
    _console.print(Text(msg, style="bold cyan"))

def warn(msg: str):
    _console.print(Text(msg, style="bold yellow"))

def error(msg: str):
    _console.print(Text(msg, style="bold red"))
