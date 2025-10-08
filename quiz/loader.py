"""Utility for loading the quiz configuration from JSON."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .models import (
    ChoiceOption,
    FeedbackTemplates,
    ForcedChoiceQuestion,
    LikertQuestion,
    QuizConfig,
    QuestionBase,
    QuestionType,
    ScoringSpec,
    SingleChoiceQuestion,
    Trait,
    UISettings,
)

LOGGER = logging.getLogger(__name__)

REQUIRED_TOP_LEVEL_KEYS: tuple[str, ...] = (
    "quiz_id",
    "title",
    "traits",
    "questions",
    "scoring",
    "feedback_templates",
)


class QuizConfigError(RuntimeError):
    """Raised when the quiz configuration file fails validation."""


def _require_keys(payload: Dict[str, Any], keys: Iterable[str]) -> None:
    missing = [key for key in keys if key not in payload]
    if missing:
        raise QuizConfigError(f"Missing required keys: {', '.join(sorted(missing))}")


def _validate_weights(trait_codes: set[str], weights: Dict[str, float], *, context: str) -> None:
    unknown = set(weights) - trait_codes
    if unknown:
        raise QuizConfigError(f"Unknown trait codes {unknown} in {context}")


def _build_choice_question(
    base: Dict[str, Any],
    trait_codes: set[str],
    *,
    forced: bool = False,
) -> QuestionBase:
    options: List[ChoiceOption] = []
    seen_keys: set[str] = set()
    for opt in base.get("options", []):
        key = opt.get("key")
        if key in seen_keys:
            raise QuizConfigError(f"Duplicate option key '{key}' in question {base.get('id')}")
        seen_keys.add(key)
        weights = opt.get("weights", {})
        _validate_weights(trait_codes, weights, context=f"question {base.get('id')} option {key}")
        options.append(
            ChoiceOption(
                key=key,
                label=opt.get("label", ""),
                weights={code: float(value) for code, value in weights.items()},
            )
        )
    if forced:
        return ForcedChoiceQuestion(
            id=base["id"],
            type=base["type"],
            text=base.get("text", ""),
            options=options,
            tags=base.get("tags"),
        )
    return SingleChoiceQuestion(
        id=base["id"],
        type=base["type"],
        text=base.get("text", ""),
        options=options,
        tags=base.get("tags"),
    )


def _build_likert_question(base: Dict[str, Any], trait_codes: set[str]) -> LikertQuestion:
    scale = base.get("scale", [])
    if not scale:
        raise QuizConfigError(f"Likert question {base.get('id')} requires a scale")
    weights = base.get("weights_per_point", {})
    _validate_weights(trait_codes, weights, context=f"question {base.get('id')} weights_per_point")
    return LikertQuestion(
        id=base["id"],
        type=base["type"],
        text=base.get("text", ""),
        scale=[int(v) for v in scale],
        labels={str(k): str(v) for k, v in base.get("labels", {}).items()},
        weights_per_point={code: float(value) for code, value in weights.items()},
        tags=base.get("tags"),
    )


def _build_question(base: Dict[str, Any], trait_codes: set[str]) -> QuestionBase:
    q_type: QuestionType = base.get("type")
    if q_type not in {"single_choice", "forced_choice", "likert"}:
        raise QuizConfigError(f"Unsupported question type '{q_type}'")
    if q_type == "likert":
        return _build_likert_question(base, trait_codes)
    return _build_choice_question(base, trait_codes, forced=q_type == "forced_choice")


def load_quiz_config(path: Path) -> QuizConfig:
    """Load and validate the quiz configuration file."""

    LOGGER.info("Loading quiz configuration from %s", path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise QuizConfigError(f"Unable to read quiz configuration: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise QuizConfigError(f"Invalid JSON: {exc}") from exc

    _require_keys(data, REQUIRED_TOP_LEVEL_KEYS)

    traits_payload = data.get("traits", [])
    if not traits_payload:
        raise QuizConfigError("Quiz must define at least one trait")

    traits = [Trait(code=item["code"], name=item.get("name", item["code"])) for item in traits_payload]
    trait_codes = {trait.code for trait in traits}

    questions_payload = data.get("questions", [])
    if not questions_payload:
        raise QuizConfigError("Quiz must contain at least one question")

    seen_ids: set[str] = set()
    questions: List[QuestionBase] = []
    for q_payload in questions_payload:
        q_id = q_payload.get("id")
        if not q_id:
            raise QuizConfigError("Question missing 'id'")
        if q_id in seen_ids:
            raise QuizConfigError(f"Duplicate question id '{q_id}'")
        seen_ids.add(q_id)
        question = _build_question(q_payload, trait_codes)
        questions.append(question)

    scoring_payload = data.get("scoring", {})
    _require_keys(scoring_payload, ("trait_caps", "industrial_fit_weights", "thresholds", "normalization"))

    trait_caps = scoring_payload.get("trait_caps", {})
    industrial_weights = scoring_payload.get("industrial_fit_weights", {})
    if set(trait_caps) != trait_codes:
        raise QuizConfigError("Trait caps must be provided for all traits")
    if set(industrial_weights) != trait_codes:
        raise QuizConfigError("Industrial fit weights must be provided for all traits")

    thresholds = scoring_payload.get("thresholds", [])
    if not thresholds:
        raise QuizConfigError("At least one scoring threshold is required")

    feedback_payload = data.get("feedback_templates", {})
    _require_keys(feedback_payload, ("overall", "trait_snippets", "next_steps"))

    ui_payload = data.get("ui", {})

    config = QuizConfig(
        quiz_id=data["quiz_id"],
        title=data["title"],
        traits=traits,
        questions=questions,
        scoring=ScoringSpec(
            trait_caps={code: float(value) for code, value in trait_caps.items()},
            industrial_fit_weights={code: float(value) for code, value in industrial_weights.items()},
            thresholds=thresholds,
            normalization=scoring_payload.get("normalization", ""),
        ),
        feedback_templates=FeedbackTemplates(
            overall={key: str(value) for key, value in feedback_payload.get("overall", {}).items()},
            trait_snippets={key: str(value) for key, value in feedback_payload.get("trait_snippets", {}).items()},
            next_steps=[str(step) for step in feedback_payload.get("next_steps", [])],
        ),
        ui=UISettings(
            progress_bar=bool(ui_payload.get("progress_bar", False)),
            shuffle_within_types=bool(ui_payload.get("shuffle_within_types", False)),
            length_minutes=ui_payload.get("length_minutes"),
            skip_logic=ui_payload.get("skip_logic"),
            result_visuals=ui_payload.get("result_visuals"),
        ),
    )

    LOGGER.info("Loaded quiz '%s' with %d questions", config.quiz_id, len(config.questions))
    return config
