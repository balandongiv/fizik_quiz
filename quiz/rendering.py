"""Helpers for rendering quiz questions in templates."""

from __future__ import annotations

import itertools
import random
from typing import List

from .models import QuestionBase, QuizConfig


def order_questions(config: QuizConfig) -> List[QuestionBase]:
    """Return questions ordered according to UI settings."""

    questions = list(config.questions)
    if not config.ui.shuffle_within_types:
        return questions

    groups: dict[str, List[QuestionBase]] = {}
    order: List[str] = []
    for question in questions:
        q_type = question.type
        if q_type not in groups:
            groups[q_type] = []
            order.append(q_type)
        groups[q_type].append(question)

    rng = random.Random(config.quiz_id)
    shuffled_groups = []
    for q_type in order:
        group = groups[q_type]
        rng.shuffle(group)
        shuffled_groups.append(group)

    return list(itertools.chain.from_iterable(shuffled_groups))


def progress_context(total_questions: int) -> dict[str, int]:
    """Return a template context stub for progress bar rendering."""

    return {"total_questions": total_questions}
