"""
AcadFlow — LLM module (backward compatibility wrapper)
Delegates to centralized gemini_client via agents.
"""
import agents


def ask(system: str, user: str, max_tokens: int = 1500) -> str:
    return agents.llm(system, user, max_tokens)


def ask_json(system: str, user: str, default=None):
    text = ask(system + "\nReturn ONLY valid JSON. No prose, no markdown fences.", user)
    return agents.parse_json(text, default)
