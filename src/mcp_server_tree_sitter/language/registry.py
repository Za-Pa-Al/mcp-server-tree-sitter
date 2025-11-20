"""Language registry for tree-sitter languages."""

import logging
import threading
from typing import Any, Dict, List, Optional, Tuple, Set

from tree_sitter_language_pack import get_language, get_parser

# Import parser_cache functions inside methods to avoid circular imports
# Import global_context inside methods to avoid circular imports
from ..exceptions import LanguageNotFoundError
from ..utils.tree_sitter_types import (
    Language,
    Parser,
    ensure_language,
)

logger = logging.getLogger(__name__)


class LanguageRegistry:
    """Manages tree-sitter language parsers."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self._lock = threading.RLock()
        self.languages: Dict[str, Language] = {}
        self._language_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "jsx": "javascript",
            "tsx": "typescript",
            "rb": "ruby",
            "rs": "rust",
            "go": "go",
            "java": "java",
            "c": "c",
            "cpp": "cpp",
            "cc": "cpp",
            "h": "c",
            "hpp": "cpp",
            "cs": "c_sharp",
            "php": "php",
            "scala": "scala",
            "swift": "swift",
            "kt": "kotlin",
            "lua": "lua",
            "hs": "haskell",
            "ml": "ocaml",
            "sh": "bash",
            "yaml": "yaml",
            "yml": "yaml",
            "json": "json",
            "md": "markdown",
            "html": "html",
            "css": "css",
            "scss": "scss",
            "sass": "scss",
            "sql": "sql",
            "proto": "proto",
            "elm": "elm",
            "clj": "clojure",
            "ex": "elixir",
            "exs": "elixir",
        }

        # Discover installed tree-sitter packages
        self._installed_languages = self._discover_installed_languages()
        if self._installed_languages:
            logger.info(f"Discovered {len(self._installed_languages)} installed tree-sitter packages: {sorted(self._installed_languages)}")

        # Pre-load preferred languages if configured
        # Get dependencies within the method to avoid circular imports
        try:
            from ..di import get_container

            config = get_container().get_config()
            for lang in config.language.preferred_languages:
                try:
                    self.get_language(lang)
                except Exception as e:
                    logger.warning(f"Failed to pre-load language {lang}: {e}")
        except ImportError:
            # If dependency container isn't available yet, just skip this step
            logger.warning("Skipping pre-loading of languages due to missing dependencies")

    def _discover_installed_languages(self) -> Set[str]:
        """
        Discover installed tree-sitter language packages.

        Scans installed Python packages for tree_sitter_* packages and
        extracts display names from package metadata.

        Returns:
            Set of language names (without tree_sitter_ prefix)
        """
        discovered = set()
        self._language_display_names: Dict[str, str] = {}  # lang_id -> display name

        try:
            from importlib.metadata import distributions

            for dist in distributions():
                # Look for packages starting with tree-sitter- or tree_sitter_
                name = dist.metadata.get('Name', '')
                if name.startswith('tree-sitter-') or name.startswith('tree_sitter_'):
                    # Extract language name
                    # tree-sitter-python -> python
                    # tree_sitter_xpp -> xpp
                    lang_name = name.replace('tree-sitter-', '').replace('tree_sitter_', '').replace('-', '_')
                    if lang_name and lang_name != 'language_pack':  # Exclude the language pack itself
                        discovered.add(lang_name)

                        # Extract display name from Summary if available
                        summary = dist.metadata.get('Summary', '')
                        if summary:
                            # Try to extract clean display name
                            # "C# grammar for tree-sitter" -> "C#"
                            # "Tree-sitter grammar for Dynamics AX X++" -> "Dynamics AX X++"
                            if ' grammar for tree-sitter' in summary:
                                display_name = summary.split(' grammar for tree-sitter')[0]
                            elif 'Tree-sitter grammar for ' in summary:
                                display_name = summary.split('Tree-sitter grammar for ')[1]
                            elif 'grammar for tree-sitter' in summary.lower():
                                # More flexible extraction
                                display_name = summary.split('grammar')[0].strip()
                            else:
                                display_name = summary

                            self._language_display_names[lang_name] = display_name
                            logger.debug(f"Discovered: {name} -> {lang_name} ({display_name})")
                        else:
                            logger.debug(f"Discovered: {name} -> {lang_name}")

        except Exception as e:
            logger.warning(f"Failed to discover installed tree-sitter packages: {e}")

        return discovered

    def get_language_display_name(self, language_name: str) -> str:
        """
        Get the display name for a language.

        Args:
            language_name: Language identifier (e.g., 'xpp', 'c_sharp')

        Returns:
            Display name if available, otherwise returns the language_name
        """
        return self._language_display_names.get(language_name, language_name)

    def language_for_file(self, file_path: str) -> Optional[str]:
        """
        Detect language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Language identifier or None if unknown
        """
        ext = file_path.split(".")[-1].lower() if "." in file_path else ""
        return self._language_map.get(ext)

    def list_available_languages(self) -> List[str]:
        """
        List languages that are available via tree-sitter packages.

        Returns languages from:
        - Currently loaded languages
        - Language pack (via extension map)
        - Discovered installed tree-sitter packages

        Returns:
            List of available language identifiers
        """
        # Start with loaded languages
        available = set(self.languages.keys())

        # Add all mappable languages from our extension map
        # These correspond to the languages available in tree-sitter-language-pack
        available.update(set(self._language_map.values()))

        # Add dynamically discovered installed packages
        available.update(self._installed_languages)

        # Add frequently used languages that might not be in the map
        common_languages = [
            "python",
            "javascript",
            "typescript",
            "java",
            "c",
            "cpp",
            "go",
            "rust",
            "ruby",
            "php",
            "swift",
            "kotlin",
            "scala",
            "bash",
            "html",
            "css",
            "json",
            "yaml",
            "markdown",
            "c_sharp",
            "objective_c",
            "xml",
        ]
        available.update(common_languages)

        # Return as a sorted list
        return sorted(available)

    def list_installable_languages(self) -> List[Tuple[str, str]]:
        """
        List languages that can be installed.
        With tree-sitter-language-pack, no additional installation is needed.

        Returns:
            Empty list (all languages are available via language-pack)
        """
        return []

    def is_language_available(self, language_name: str) -> bool:
        """
        Check if a language is available in tree-sitter-language-pack.

        Args:
            language_name: Language identifier

        Returns:
            True if language is available
        """
        try:
            self.get_language(language_name)
            return True
        except Exception:
            return False

    def get_language(self, language_name: str) -> Any:
        """
        Get or load a language by name from tree-sitter packages.

        First tries tree-sitter-language-pack, then falls back to standalone packages.

        Args:
            language_name: Language identifier

        Returns:
            Tree-sitter Language object

        Raises:
            LanguageNotFoundError: If language cannot be loaded
        """
        with self._lock:
            if language_name in self.languages:
                return self.languages[language_name]

            try:
                # Try language pack first
                # Type ignore: language_name is dynamic but tree-sitter-language-pack
                # types expect a Literal with specific language names
                language_obj = get_language(language_name)  # type: ignore

                # Cast to our Language type for type safety
                language = ensure_language(language_obj)
                self.languages[language_name] = language
                return language
            except Exception as pack_error:
                # Fall back to standalone tree-sitter package
                try:
                    import importlib

                    # Try to import tree_sitter_{language_name}
                    module = importlib.import_module(f"tree_sitter_{language_name}")

                    # Get the language() function from the module
                    if hasattr(module, 'language'):
                        language_capsule = module.language()
                        # Wrap capsule in Language object if needed
                        language = ensure_language(language_capsule)
                        self.languages[language_name] = language
                        logger.info(f"Loaded language {language_name} from standalone package")
                        return language
                    else:
                        raise AttributeError(f"Module tree_sitter_{language_name} has no 'language' function")

                except (ImportError, AttributeError) as standalone_error:
                    raise LanguageNotFoundError(
                        f"Language {language_name} not available. "
                        f"Tried language-pack: {pack_error}. "
                        f"Tried standalone package: {standalone_error}"
                    ) from pack_error

    def get_parser(self, language_name: str) -> Parser:
        """
        Get a parser for the specified language.

        Args:
            language_name: Language identifier

        Returns:
            Tree-sitter Parser configured for the language
        """
        try:
            # Try to get a parser directly from the language pack
            # Type ignore: language_name is dynamic but tree-sitter-language-pack
            # types expect a Literal with specific language names
            parser = get_parser(language_name)  # type: ignore
            return parser
        except Exception:
            # Fall back to older method, importing at runtime to avoid circular imports
            from ..cache.parser_cache import get_cached_parser

            language = self.get_language(language_name)
            return get_cached_parser(language)
