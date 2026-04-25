import re

# Common academic/complex words and their simpler alternatives
SIMPLIFICATION_MAP = {
    "utilize": "use",
    "therefore": "so",
    "however": "but",
    "subsequently": "then",
    "consequently": "as a result",
    "approximately": "about",
    "demonstrate": "show",
    "facilitate": "help",
    "implement": "do",
    "obtain": "get",
    "assist": "help",
    "commence": "start",
    "terminate": "end",
    "comprehend": "understand",
    "sufficient": "enough",
    "numerous": "many",
    "significant": "important",
    "purchase": "buy",
    "require": "need",
    "attempt": "try",
    "inquire": "ask",
    "provide": "give",
    "indicate": "show",
    "regarding": "about",
    "additional": "more",
    "eliminate": "remove",
    "determine": "find out",
    "manufacture": "make",
    "construct": "build",
    "investigate": "look into",
    "accomplish": "achieve",
}


def replace_complex_words(text: str) -> str:
    """Replace complex/academic words with simpler synonyms."""
    for complex_word, simple_word in SIMPLIFICATION_MAP.items():
        pattern = re.compile(r'\b' + complex_word + r'\b', re.IGNORECASE)
        text = pattern.sub(simple_word, text)
    return text


def split_into_sentences(text: str) -> list:
    """Split text into individual sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def shorten_sentence(sentence: str, max_words: int = 20) -> str:
    """
    Shorten a sentence if it exceeds max_words by keeping
    only the first clause (before comma or conjunction).
    """
    words = sentence.split()
    if len(words) <= max_words:
        return sentence

    # Try to cut at a natural break point
    for delimiter in [", which", ", that", ", because", ", and", ", but", ", so"]:
        if delimiter in sentence:
            return sentence.split(delimiter)[0].strip() + "."

    # Hard truncate as fallback
    return " ".join(words[:max_words]) + "..."


def simplify_text(text: str) -> dict:
    """
    Simplify input text into shorter, more understandable sentences.

    Args:
        text (str): Original teacher speech or input text.

    Returns:
        dict: {
            "success": bool,
            "simplified_text": str,
            "bullet_points": list,
            "error": str or None
        }
    """
    if not text or not text.strip():
        return {
            "success": False,
            "simplified_text": "",
            "bullet_points": [],
            "error": "No text provided for simplification."
        }

    try:
        # Step 1: Replace complex words
        simplified = replace_complex_words(text)

        # Step 2: Split into sentences
        sentences = split_into_sentences(simplified)

        # Step 3: Shorten long sentences
        shortened = [shorten_sentence(s) for s in sentences]

        # Rejoin into paragraph
        simplified_paragraph = " ".join(shortened)

        return {
            "success": True,
            "simplified_text": simplified_paragraph,
            "bullet_points": shortened,
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "simplified_text": text,
            "bullet_points": [],
            "error": f"Simplification error: {str(e)}"
        }
