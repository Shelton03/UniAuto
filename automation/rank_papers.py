from __future__ import annotations
import re
from datetime import date, timedelta
from automation.config import names

AI_CONTEXT = {"ai", "artificial", "intelligence", "machine", "learning", "model", "models", "llm", "llms", "neural", "deep", "algorithm", "algorithms", "computational"}

def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.casefold()))

def _contains_phrase(phrase: str, text: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(phrase.casefold()) + r"(?!\w)", text))

def _match_text(tracked: list[str], text: str) -> list[str]:
    words = _words(text)
    matches = []
    for name in tracked:
        # A standalone broad term such as "Reasoning" is only research-ML
        # content when the same record has an AI/ML signal. This prevents
        # religious, legal, and philosophical uses of the word from matching.
        if _contains_phrase(name, text) and (len(_words(name)) > 1 or words & AI_CONTEXT):
            matches.append(name)
    return matches

def _match_question(tracked: list[str], text: str) -> list[str]:
    """Match a full question where possible, otherwise all meaningful words."""
    hits = []
    for question in tracked:
        phrase = question.casefold()
        words = [word for word in _words(phrase) if (len(word) > 2 or word == "ai") and word not in {"and", "the", "with", "for", "are"}]
        if _contains_phrase(phrase, text) or (words and all(word in _words(text) for word in words)):
            hits.append(question)
    return hits

def _match_universities(tracked: list[str], metadata: list[str], text: str) -> list[str]:
    """Only tracked names count; OpenAlex may return dozens of unrelated affiliations."""
    matched = []
    for name in tracked:
        needle = name.casefold()
        if needle in text or any(needle in institution.casefold() for institution in metadata):
            matched.append(name)
    return matched

def rank_item(item: dict, config: dict) -> dict:
    text = " ".join([item.get("title", ""), item.get("abstract", ""), " ".join(item.get("authors", []))]).casefold()
    item["topics"] = _match_text(names(config, "research_areas"), text)
    item["researchers"] = _match_text(names(config, "researchers"), text)
    item["universities"] = _match_universities(names(config, "universities"), item.get("universities", []), text)
    question_matches = _match_question(names(config, "research_questions"), text)
    item["questions"] = question_matches
    # A university affiliation by itself does not make a paper relevant to the
    # user's research. It can boost a content/researcher match but cannot cause
    # an unrelated biomedical, humanities, or clinical paper to reach Review.
    item["review_eligible"] = bool(item["topics"] or item["researchers"] or question_matches)
    score = len(question_matches) + len(item["topics"]) + len(item["researchers"])
    try:
        if date.fromisoformat((item.get("published_date") or "")[:10]) >= date.today() - timedelta(days=14): score += 0.5
    except ValueError: pass
    item["relevance_score"] = score
    return item

def rank_items(items: list[dict], config: dict) -> list[dict]:
    return sorted((rank_item(item, config) for item in items), key=lambda x: (x["review_eligible"], x["relevance_score"]), reverse=True)
