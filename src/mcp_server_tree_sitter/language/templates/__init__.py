"""Language-specific query templates collection."""

import importlib
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

def _discover_templates() -> Dict[str, Dict[str, str]]:
    """Dynamically discover and load all template modules.

    Scans the templates directory for *.py files (excluding __init__.py),
    imports each module, and extracts the TEMPLATES dict.

    Also discovers .scm query files from installed tree-sitter packages.

    Returns:
        Dict mapping language names to their template dictionaries
    """
    templates: Dict[str, Dict[str, str]] = {}
    templates_dir = Path(__file__).parent

    # Find all Python files in the templates directory
    for template_file in templates_dir.glob("*.py"):
        # Skip __init__.py and __pycache__
        if template_file.name.startswith("_"):
            continue

        # Language name is the file name without .py extension
        language_name = template_file.stem

        try:
            # Dynamically import the template module
            module = importlib.import_module(f".{language_name}", package=__package__)

            # Extract TEMPLATES dict from the module
            if hasattr(module, "TEMPLATES"):
                templates[language_name] = module.TEMPLATES
                logger.debug(f"Loaded template from .py: {language_name}")
            else:
                logger.warning(f"Template module {language_name} missing TEMPLATES dict")

        except Exception as e:
            logger.warning(f"Failed to load template {language_name}: {e}")

    # Discover .scm files from installed tree-sitter packages
    _discover_scm_queries(templates)

    logger.info(f"Discovered {len(templates)} query templates")
    return templates


def _discover_scm_queries(templates: Dict[str, Dict[str, str]]) -> None:
    """Discover .scm query files from installed tree-sitter packages.

    Looks for tree_sitter_* packages with queries/ directories and loads .scm files.

    Args:
        templates: Dict to update with discovered queries
    """
    try:
        from importlib.metadata import distributions

        for dist in distributions():
            name = dist.metadata.get('Name', '')
            if name.startswith('tree-sitter-') or name.startswith('tree_sitter_'):
                # Extract language name (e.g., tree-sitter-xpo -> xpo)
                lang_name = name.replace('tree-sitter-', '').replace('tree_sitter_', '').replace('-', '_')

                if lang_name and lang_name != 'language_pack':
                    try:
                        # Try to import the package
                        module = importlib.import_module(f"tree_sitter_{lang_name}")

                        # Find package directory
                        if hasattr(module, '__file__') and module.__file__:
                            # Module is in bindings/python/tree_sitter_*/
                            # We need to go up to the root (bindings/python/tree_sitter_* -> bindings/python -> bindings -> root)
                            module_path = Path(module.__file__).parent

                            # Try multiple possible locations for queries directory
                            possible_queries_dirs = [
                                module_path.parent.parent.parent / 'queries',  # Root level (for tree-sitter packages)
                                module_path.parent / 'queries',  # Package level
                                module_path / 'queries',  # Module level
                            ]

                            queries_dir = None
                            for possible_dir in possible_queries_dirs:
                                if possible_dir.exists() and possible_dir.is_dir():
                                    queries_dir = possible_dir
                                    break

                            if queries_dir:
                                # Load all .scm files
                                scm_templates: Dict[str, str] = {}
                                for scm_file in queries_dir.glob("*.scm"):
                                    template_name = scm_file.stem.replace('-', '_')
                                    try:
                                        scm_templates[template_name] = scm_file.read_text(encoding='utf-8')
                                        logger.debug(f"Loaded .scm query: {lang_name}/{template_name}")
                                    except Exception as e:
                                        logger.warning(f"Failed to load {scm_file}: {e}")

                                if scm_templates:
                                    # Merge with existing templates or create new
                                    if lang_name in templates:
                                        templates[lang_name].update(scm_templates)
                                    else:
                                        templates[lang_name] = scm_templates
                                    logger.info(f"Loaded {len(scm_templates)} .scm queries for {lang_name}")

                    except ImportError:
                        # Package not importable, skip
                        pass
                    except Exception as e:
                        logger.debug(f"Could not load queries for {lang_name}: {e}")

    except Exception as e:
        logger.warning(f"Failed to discover .scm queries: {e}")


# Auto-discover all templates
QUERY_TEMPLATES: Dict[str, Dict[str, str]] = _discover_templates()
