"""Flask entrypoint for the Industrial Physics quiz application."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from quiz.forms import AnswerValidationError, parse_answers
from quiz.loader import QuizConfigError, load_quiz_config
from quiz.models import QuizConfig
from quiz.rendering import order_questions, progress_context
from quiz.scoring import (
    apply_caps,
    compute_fit_score,
    compute_trait_scores,
    compose_feedback,
    map_threshold,
)
from quiz.utils import normalize_scores, trait_code_to_name

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
QUIZ_SCHEMA_PATH = DATA_DIR / "quiz_schema.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
LOGGER = logging.getLogger(__name__)

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
app.secret_key = os.getenv("APP_SECRET", "change-me")


def _load_config() -> QuizConfig:
    LOGGER.info("Loading quiz configuration for request")
    return load_quiz_config(QUIZ_SCHEMA_PATH)


@app.errorhandler(QuizConfigError)
def handle_config_error(error: QuizConfigError):  # type: ignore[override]
    LOGGER.exception("Quiz configuration error: %s", error)
    return (
        render_template("error.html", message="Quiz temporarily unavailable."),
        500,
    )


@app.route("/")
def index():
    LOGGER.info("Handling index route")
    config = _load_config()
    return render_template("index.html", config=config)


@app.route("/quiz", methods=["GET", "POST"])
def quiz_view():
    LOGGER.info("Handling quiz route")
    config = _load_config()
    ordered_questions = order_questions(config)
    if request.method == "POST":
        try:
            answers = parse_answers(config, request.form)
        except AnswerValidationError as exc:
            flash(str(exc), "error")
            return render_template(
                "quiz.html",
                config=config,
                questions=ordered_questions,
                progress=progress_context(len(ordered_questions)),
                previous_answers=request.form,
            )
        session["quiz_id"] = config.quiz_id
        session["answers"] = answers
        return redirect(url_for("result"))

    previous_answers = session.get("answers") if session.get("quiz_id") == config.quiz_id else None
    return render_template(
        "quiz.html",
        config=config,
        questions=ordered_questions,
        progress=progress_context(len(ordered_questions)),
        previous_answers=previous_answers,
    )


@app.route("/result")
def result():
    LOGGER.info("Handling result route")
    config = _load_config()
    answers = session.get("answers")
    if not answers or session.get("quiz_id") != config.quiz_id:
        flash("Please complete the quiz first.", "error")
        return redirect(url_for("quiz_view"))

    raw_scores = compute_trait_scores(config, answers)
    capped_scores = apply_caps(config, raw_scores)
    normalized = normalize_scores(config, capped_scores)
    fit_score = compute_fit_score(config, capped_scores)
    label = map_threshold(config, fit_score)
    feedback = compose_feedback(config, capped_scores, label)

    trait_names = trait_code_to_name(config)
    trait_display = []
    for trait in config.traits:
        code = trait.code
        trait_display.append(
            {
                "code": code,
                "name": trait_names.get(code, code),
                "score": capped_scores.get(code, 0.0),
                "normalized": normalized.get(code, 0.0),
            }
        )

    return render_template(
        "result.html",
        config=config,
        fit_score=round(fit_score, 1),
        label=label,
        normalized=normalized,
        traits=trait_display,
        feedback=feedback,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=False)
