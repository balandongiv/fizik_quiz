"""Dataclasses describing the quiz configuration domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

QuestionType = Literal["single_choice", "forced_choice", "likert"]


@dataclass(slots=True)
class Trait:
    """Represents a trait measured by the quiz."""

    code: str
    name: str


@dataclass(slots=True)
class ChoiceOption:
    """Represents a selectable option for choice-based questions."""

    key: str
    label: str
    weights: Dict[str, float]


@dataclass(slots=True)
class QuestionBase:
    """Base fields shared by all question types."""

    id: str
    type: QuestionType
    text: str
    tags: Optional[List[str]] = None


@dataclass(slots=True)
class SingleChoiceQuestion(QuestionBase):
    """Single-choice question where one option is selected."""

    options: List[ChoiceOption] = field(default_factory=list)


@dataclass(slots=True)
class ForcedChoiceQuestion(QuestionBase):
    """Forced-choice question with two contrasted options."""

    options: List[ChoiceOption] = field(default_factory=list)


@dataclass(slots=True)
class LikertQuestion(QuestionBase):
    """Likert scale question scored by selected point."""

    scale: List[int] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    weights_per_point: Dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class ScoringSpec:
    trait_caps: Dict[str, float]
    industrial_fit_weights: Dict[str, float]
    thresholds: List[Dict[str, Any]]
    normalization: str


@dataclass(slots=True)
class FeedbackTemplates:
    overall: Dict[str, str]
    trait_snippets: Dict[str, str]
    next_steps: List[str]


@dataclass(slots=True)
class UISettings:
    progress_bar: bool
    shuffle_within_types: bool
    length_minutes: Optional[int] = None
    skip_logic: Optional[List[Dict[str, Any]]] = None
    result_visuals: Optional[List[str]] = None


@dataclass(slots=True)
class QuizConfig:
    quiz_id: str
    title: str
    traits: List[Trait]
    questions: List[QuestionBase]
    scoring: ScoringSpec
    feedback_templates: FeedbackTemplates
    ui: UISettings


Question = SingleChoiceQuestion | ForcedChoiceQuestion | LikertQuestion
