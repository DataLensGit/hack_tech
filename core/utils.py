import os
import inspect
from dotenv import load_dotenv

# Környezeti változók betöltése a .env fájlból
load_dotenv()

# DEBUG flag beállítása az .env fájlból
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

def debugprint(*args, **kwargs):
    """Csak akkor printel, ha a DEBUG aktív, és hozzáfűzi a hívó .py fájl nevét, illetve indentál a hívások szintje szerint."""
    if DEBUG:
        # Hívó információk lekérése
        stack = inspect.stack()
        caller = stack[1]  # A közvetlen hívó
        caller_filename = caller.filename.split(os.sep)[-1]  # Csak a fájlnév

        # Hívási mélység számítása (indentálás)
        indent_level = len(stack) - 1
        indent = '    ' * (indent_level - 1)  # 4 szóköz per hívási szint

        # Print kimenet összeállítása
        print(f"{indent}{caller_filename}: ", *args, **kwargs)
