"""Quiz package initialization."""

from .loader import load_quiz_config
from .models import QuizConfig

__all__ = ["load_quiz_config", "QuizConfig"]
