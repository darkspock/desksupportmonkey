import json
import logging

logger = logging.getLogger(__name__)

CLASSIFIER_MODEL = "llama-3.1-8b-instant"


def _call_classifier(
    prompt: str, api_key: str, timeout: float = 3.0
) -> list[str] | None:
    """Raw Groq API call to classify help keys. Returns list of key names or None."""
    try:
        import openai

        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
            timeout=timeout,
        )
        response = client.chat.completions.create(
            model=CLASSIFIER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200,
        )
        content = response.choices[0].message.content
        if not content:
            return None
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return [str(k) for k in parsed]
        return None
    except Exception as e:
        logger.warning("Help key classifier failed: %s", e)
        return None


def classify_help_keys(
    all_keys: dict[str, str],
    user_message: str,
    groq_api_key: str,
    timeout: float = 3.0,
) -> dict[str, str]:
    """Select relevant help keys for a user message using a fast classifier.

    Sends only key names (~600 tokens) to Groq 8b to identify 5-10 relevant keys.
    Falls back to all keys on any failure.
    """
    if not groq_api_key or not user_message.strip():
        return all_keys

    key_names = sorted(all_keys.keys())
    key_index = "\n".join(key_names)

    prompt = (
        "You are a help-topic classifier. Given the list of help topic keys below "
        "and a user question, return a JSON array of the 5-10 most relevant key names. "
        "Return ONLY the JSON array, no other text.\n\n"
        f"Available keys:\n{key_index}\n\n"
        f"User question: {user_message}\n\n"
        "Relevant keys (JSON array):"
    )

    selected = _call_classifier(prompt, groq_api_key, timeout)

    if not selected or not isinstance(selected, list):
        return all_keys

    # Always include help.default as baseline
    if "help.default" in all_keys and "help.default" not in selected:
        selected.append("help.default")

    # Sanity check: if fewer than 2 valid keys, return all
    valid_keys = {k: all_keys[k] for k in selected if k in all_keys}
    if len(valid_keys) < 2:
        return all_keys

    return valid_keys
