import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_help_content: dict[str, str] | None = None


def _load_help_content() -> dict[str, str]:
    """Extract help.* keys from en.ts locale file."""
    global _help_content
    if _help_content is not None:
        return _help_content

    _help_content = {}
    locale_path = Path(__file__).resolve().parents[4] / "web" / "app" / "src" / "locales" / "en.ts"
    try:
        text = locale_path.read_text(encoding="utf-8")
        for match in re.finditer(r"'(help\.\w+)':\s*'([^']*(?:\\'[^']*)*)'", text):
            key = match.group(1)
            value = match.group(2).replace("\\'", "'")
            _help_content[key] = value
    except Exception as e:
        logger.warning("Could not load help content: %s", e)
    return _help_content


def build_system_prompt(
    company_name: str,
    plan_tier: str,
    enabled_modules: list[str],
    relevant_keys: dict[str, str] | None = None,
) -> str:
    """Build the AI assistant system prompt with help content and company context.

    Args:
        relevant_keys: Pre-filtered help keys to use instead of all keys.
            When None, loads and uses all keys (backward compatible).
    """
    help_content = relevant_keys if relevant_keys is not None else _load_help_content()

    help_text = "\n".join(
        f"- {key.replace('help.', '')}: {value}"
        for key, value in sorted(help_content.items())
    )

    modules_text = ", ".join(enabled_modules) if enabled_modules else "all modules"

    return f"""You are the DSM Control support assistant — a helpful, concise AI that answers questions about the DSM Control IT Service Desk & Asset Inventory platform.

## Company Context
- Company: {company_name}
- Plan: {plan_tier}
- Enabled modules: {modules_text}

## Your Knowledge Base
{help_text}

## Rules
- Answer questions about DSM Control features, workflows, and configuration
- Be concise and helpful — aim for 2-4 sentences unless the user asks for detail
- If the user's plan doesn't include a feature, mention they may need to upgrade
- If you're unsure or the question is about a bug, billing, or account issue, suggest creating a support ticket
- Never make up features that don't exist in DSM Control
- Respond in the same language the user writes in
- Do not answer questions unrelated to DSM Control"""


def select_relevant_help_keys(user_message: str) -> dict[str, str] | None:
    """Load all help keys and classify them for relevance to the user message.

    Returns a filtered dict of relevant keys, or None on failure (caller
    should fall back to using all keys via build_system_prompt default).
    """
    from core.config import settings
    from src.support_bc.ai_assistant.infrastructure.help_key_classifier import (
        classify_help_keys,
    )

    all_keys = _load_help_content()
    if not all_keys:
        return None

    groq_api_key = settings.ai.GROQ_API_KEY
    if not groq_api_key:
        return None

    try:
        result = classify_help_keys(all_keys, user_message, groq_api_key)
        # If classifier returned all keys, return None so caller uses default path
        if result is all_keys:
            return None
        logger.info(
            "Help key classifier selected %d/%d keys", len(result), len(all_keys)
        )
        return result
    except Exception as e:
        logger.warning("Help key selection failed: %s", e)
        return None
