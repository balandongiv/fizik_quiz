"""Scoring utilities for the Industrial Physics quiz."""

from __future__ import annotations

import statistics
from typing import Any, Dict, List

from .models import ForcedChoiceQuestion, LikertQuestion, QuizConfig, SingleChoiceQuestion


def _ensure_trait_keys(config: QuizConfig) -> List[str]:
    return [trait.code for trait in config.traits]


def compute_trait_scores(config: QuizConfig, answers: Dict[str, Any]) -> Dict[str, float]:
    """Compute raw trait scores from submitted answers."""

    trait_scores = {trait.code: 0.0 for trait in config.traits}
    for question in config.questions:
        answer = answers.get(question.id)
        if answer is None:
            continue
        if isinstance(question, (SingleChoiceQuestion, ForcedChoiceQuestion)):
            for option in question.options:
                if option.key == answer:
                    for code, value in option.weights.items():
                        trait_scores[code] += float(value)
                    break
        elif isinstance(question, LikertQuestion):
            if not isinstance(answer, int):
                continue
            for code, weight in question.weights_per_point.items():
                trait_scores[code] += float(weight) * answer
    return trait_scores


def apply_caps(config: QuizConfig, raw: Dict[str, float]) -> Dict[str, float]:
    """Apply trait caps defined in the configuration."""

    capped = {}
    for code, value in raw.items():
        cap = config.scoring.trait_caps.get(code)
        if cap is None:
            cap = value
        capped[code] = min(value, cap)
    return capped


def compute_fit_score(config: QuizConfig, capped: Dict[str, float]) -> float:
    """Compute the overall Industrial Physics fit score on a 0-20 scale."""

    weights = config.scoring.industrial_fit_weights
    total_weight = sum(weights.values()) or 1.0
    normalized_weight = {code: weight / total_weight for code, weight in weights.items()}

    score = 0.0
    for code, weight in normalized_weight.items():
        cap = config.scoring.trait_caps.get(code, 1.0) or 1.0
        normalized_trait = capped.get(code, 0.0) / cap
        score += weight * normalized_trait
    return score * 20.0


def map_threshold(config: QuizConfig, fit_score: float) -> str:
    """Map the fit score to a descriptive label using configured thresholds."""

    thresholds = sorted(
        config.scoring.thresholds,
        key=lambda item: item.get("min_score", 0),
        reverse=True,
    )
    for threshold in thresholds:
        if fit_score >= float(threshold.get("min_score", 0)):
            return str(threshold.get("label", ""))
    return str(thresholds[-1].get("label", "")) if thresholds else ""


def compose_feedback(config: QuizConfig, capped: Dict[str, float], label: str) -> Dict[str, Any]:
    """Compose human-readable feedback details based on scores and tier."""

    trait_codes = _ensure_trait_keys(config)
    trait_caps = config.scoring.trait_caps
    normalized = {
        code: (capped.get(code, 0.0) / (trait_caps.get(code) or 1.0))
        for code in trait_codes
    }

    sorted_traits = sorted(trait_codes, key=lambda code: normalized.get(code, 0.0), reverse=True)
    trait_lookup = {trait.code: trait.name for trait in config.traits}
    top_traits = [trait_lookup.get(code, code) for code in sorted_traits[:3]]

    if label == "Strong Fit for Industrial Physics":
        template_key = "strong"
    elif label == "Potential Fit — Explore Further":
        template_key = "potential"
    else:
        template_key = "explore"

    overall_templates = config.feedback_templates.overall
    overall_template = overall_templates.get(template_key, "")
    overall_text = overall_template.replace("{{TOP_TRAITS}}", ", ".join(top_traits))

    normalized_values = list(normalized.values()) or [0.0]
    median_value = statistics.median(normalized_values)

    snippets: List[str] = []
    for code in sorted_traits:
        value = normalized.get(code, 0.0)
        snippet = config.feedback_templates.trait_snippets.get(code)
        if snippet and value >= median_value:
            snippets.append(snippet)
    if not snippets:
        for code in sorted_traits[:2]:
            snippet = config.feedback_templates.trait_snippets.get(code)
            if snippet:
                snippets.append(snippet)

    return {
        "overall_text": overall_text,
        "top_traits": top_traits,
        "trait_snippets": snippets,
        "next_steps": list(config.feedback_templates.next_steps),
    }
