"""Form parsing helpers for the quiz application."""

from __future__ import annotations

from typing import Any, Dict

from werkzeug.datastructures import ImmutableMultiDict

from .models import ForcedChoiceQuestion, LikertQuestion, QuizConfig, SingleChoiceQuestion


class AnswerValidationError(ValueError):
    """Raised when submitted answers fail validation."""


def parse_answers(config: QuizConfig, form: ImmutableMultiDict) -> Dict[str, Any]:
    """Validate and normalize answers submitted from the quiz form."""

    answers: Dict[str, Any] = {}

    for question in config.questions:
        value = form.get(question.id)
        if value is None or value == "":
            raise AnswerValidationError(f"Question {question.id} is required.")

        if isinstance(question, (SingleChoiceQuestion, ForcedChoiceQuestion)):
            option_keys = {opt.key for opt in question.options}
            if value not in option_keys:
                raise AnswerValidationError(
                    f"Invalid option for question {question.id}."
                )
            answers[question.id] = value
        elif isinstance(question, LikertQuestion):
            try:
                numeric_value = int(value)
            except ValueError as exc:
                raise AnswerValidationError(
                    f"Invalid response for question {question.id}."
                ) from exc
            if numeric_value not in question.scale:
                raise AnswerValidationError(
                    f"Selected value for question {question.id} is outside the allowed scale."
                )
            answers[question.id] = numeric_value
        else:  # pragma: no cover - defensive branch
            raise AnswerValidationError(f"Unsupported question type {question.type}.")

    return answers
