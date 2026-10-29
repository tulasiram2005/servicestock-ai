"""Provider-reported observations, never inferred billing or token estimates."""
FIELDS = {
    'gemini': ('usageMetadata', {'input_tokens':'promptTokenCount','output_tokens':'candidatesTokenCount','thinking_tokens':'thoughtsTokenCount','total_tokens':'totalTokenCount'}),
    'groq': ('usage', {'input_tokens':'prompt_tokens','output_tokens':'completion_tokens','total_tokens':'total_tokens'}),
    'openai-local': ('usage', {'input_tokens':'prompt_tokens','output_tokens':'completion_tokens','total_tokens':'total_tokens'}),
    'ollama': (None, {'input_tokens':'prompt_eval_count','output_tokens':'eval_count'}),
}


def reported_tokens(provider, envelope):
    container, fields = FIELDS[provider]
    source = envelope.get(container, {}) if container else envelope
    if not isinstance(source, dict):
        return {}
    # Missing, boolean, fractional, negative or implausible metadata is unavailable.
    return {name: source[field] for name, field in fields.items()
            if type(source.get(field)) is int and 0 <= source[field] <= 1_000_000_000}
