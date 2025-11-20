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
                logger.debug(f"Loaded template: {language_name}")
            else:
                logger.warning(f"Template module {language_name} missing TEMPLATES dict")

        except Exception as e:
            logger.warning(f"Failed to load template {language_name}: {e}")

    logger.info(f"Discovered {len(templates)} query templates")
    return templates


# Auto-discover all templates
QUERY_TEMPLATES: Dict[str, Dict[str, str]] = _discover_templates()
