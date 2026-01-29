from tree_sitter import Language, Parser
from typing import Literal

import tree_sitter_bash as tsbash
import tree_sitter_cpp as tscpp
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjavascript
import tree_sitter_python as tspython
import tree_sitter_rust as tsrust
import tree_sitter_zig as tszig

LanguageName = Literal[
    "bash",
    "cpp",
    "go",
    "java",
    "javascript",
    "python",
    "rust",
    "zig",
]

LANGUAGES = {
    "bash": Language(tsbash.language()),
    "cpp": Language(tscpp.language()),
    "go": Language(tsgo.language()),
    "java": Language(tsjava.language()),
    "javascript": Language(tsjavascript.language()),
    "python": Language(tspython.language()),
    "rust": Language(tsrust.language()),
    "zig": Language(tszig.language()),
}


class TreeSitter:
    """A wrapper around the tree-sitter parser."""

    def __init__(self, language: LanguageName = "python"):
        """Initializes the parser with a specific language."""
        self._parser = Parser(LANGUAGES[language])

    def set_language(self, language: LanguageName):
        """Sets the language of the parser.

        This creates a new parser object for the specified language.
        """
        if language in LANGUAGES:
            del self._parser
            self._parser = Parser(LANGUAGES[language])
        else:
            raise ValueError(f"Unsupported language: {language}")

    def parse(self, code: str):
        """Parses the given code string and returns the Syntax Tree."""
        # Tree-sitter expects bytes for the source code
        return self._parser.parse(bytes(code, "utf8"))
