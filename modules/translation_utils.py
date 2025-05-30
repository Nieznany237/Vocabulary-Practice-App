"""
translation_utils.py

Helpers for loading and accessing translation dictionaries for the Vocabulary Practice App.
"""

from functools import lru_cache

# --- Translation loading logic ---
def load_translations(language_code):
    """
    Loads the appropriate translation dictionary based on the language code.
    Defaults to English if the code is not recognized or if Polish translations are missing.
    Args:
        language_code (str): Language code, e.g. 'en' or 'pl'.
    Returns:
        dict: The translation dictionary for the selected language.
    """
    if language_code == "pl":
        try:
            from translation import TRANSLATIONS_PL as TRANSLATIONS
        except ImportError:
            print("[WARNING]: Polish translations not found. Falling back to English.")
            from translation import TRANSLATIONS_EN as TRANSLATIONS
    else:
        from translation import TRANSLATIONS_EN as TRANSLATIONS
    return TRANSLATIONS

# Import both translation dictionaries for fallback/reference
try:
    from translation import TRANSLATIONS_PL, TRANSLATIONS_EN
except ImportError:
    TRANSLATIONS_PL = TRANSLATIONS_EN = {}

# This global variable is set by the main app after language selection.
# The main app should do:
#   import modules.translation_utils
#   modules.translation_utils.TRANSLATIONS = load_translations(language_code)
TRANSLATIONS = TRANSLATIONS_EN

# --- Translation path helper ---
@lru_cache(maxsize=None)
def t_path(path):
    """
    Retrieves a translation value from the TRANSLATIONS dictionary using a dot-separated path.
    Args:
        path (str): Dot-separated path to the translation (e.g., "menubar.file.file")
    Returns:
        str: The translated string if found, or a placeholder string in format "[path]" if not found
    Note:
        This function depends on the global TRANSLATIONS variable, which must be set before use.
    """
    keys = path.split(".")
    value = TRANSLATIONS
    try:
        for key in keys:
            value = value[key]
        return value
    except KeyError:
        print(f"[WARNING] Translation not found for path: {path}")
        return f"[{path}]"
