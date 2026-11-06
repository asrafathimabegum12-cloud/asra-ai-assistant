from __future__ import annotations

from typing import Any

QUESTION_BANK: dict[str, list[dict[str, Any]]] = {
    "Python": [
        {
            "id": "python-1",
            "question": "Which of the following is the correct way to define a function in Python?",
            "options": [
                "def myFunction():",
                "function myFunction():",
                "create myFunction():",
                "func myFunction():",
            ],
            "correct_answer": "A",
            "explanation": "Python uses the `def` keyword followed by the function name and parentheses.",
        },
        {
            "id": "python-2",
            "question": "What is the result of `len([1, 2, 3, 4])`?",
            "options": ["3", "4", "5", "6"],
            "correct_answer": "B",
            "explanation": "The list has four elements, so `len()` returns 4.",
        },
        {
            "id": "python-3",
            "question": "Which data type is best for storing unique values without duplicates?",
            "options": ["List", "Tuple", "Set", "Dictionary"],
            "correct_answer": "C",
            "explanation": "A set stores unique values and automatically removes duplicates.",
        },
    ],
    "SQL": [
        {
            "id": "sql-1",
            "question": "Which SQL command is used to retrieve data from a table?",
            "options": ["UPDATE", "SELECT", "DELETE", "INSERT"],
            "correct_answer": "B",
            "explanation": "`SELECT` is used to query and retrieve rows from a table.",
        },
        {
            "id": "sql-2",
            "question": "Which clause filters rows in a SQL query?",
            "options": ["ORDER BY", "GROUP BY", "WHERE", "JOIN"],
            "correct_answer": "C",
            "explanation": "The `WHERE` clause filters rows before grouping or sorting.",
        },
        {
            "id": "sql-3",
            "question": "What does `COUNT(*)` return?",
            "options": ["The number of distinct values", "The number of rows", "The average value", "The maximum value"],
            "correct_answer": "B",
            "explanation": "`COUNT(*)` counts every row returned by the query.",
        },
    ],
    "Aptitude": [
        {
            "id": "aptitude-1",
            "question": "If a train travels 60 km in 1 hour, what is its speed in km/h?",
            "options": ["30", "45", "60", "90"],
            "correct_answer": "C",
            "explanation": "Speed equals distance divided by time, so 60 ÷ 1 = 60 km/h.",
        },
        {
            "id": "aptitude-2",
            "question": "What is 25% of 200?",
            "options": ["25", "50", "75", "100"],
            "correct_answer": "B",
            "explanation": "25% of 200 is 0.25 × 200 = 50.",
        },
        {
            "id": "aptitude-3",
            "question": "If 5 workers complete a job in 10 days, how many days will 10 workers need at the same rate?",
            "options": ["2", "5", "10", "20"],
            "correct_answer": "B",
            "explanation": "More workers means fewer days; the workload is halved, so 5 days.",
        },
    ],
    "Data Science": [
        {
            "id": "ds-1",
            "question": "Which metric is commonly used to evaluate classification accuracy?",
            "options": ["Mean absolute error", "Accuracy score", "Median", "Standard deviation"],
            "correct_answer": "B",
            "explanation": "Accuracy is a common measure for classification performance.",
        },
        {
            "id": "ds-2",
            "question": "Which library is commonly used for data manipulation in Python?",
            "options": ["TensorFlow", "Pandas", "Flask", "Requests"],
            "correct_answer": "B",
            "explanation": "Pandas is widely used for tabular data manipulation and analysis.",
        },
        {
            "id": "ds-3",
            "question": "Which step usually comes first in a data science workflow?",
            "options": ["Model deployment", "Data cleaning", "Feature selection", "Dashboard design"],
            "correct_answer": "B",
            "explanation": "Data cleaning is usually the first major step before analysis and modeling.",
        },
    ],
}

SUBJECTS = list(QUESTION_BANK.keys())


def normalize_subject(subject: str | None) -> str | None:
    if subject is None:
        return None
    cleaned = subject.strip()
    if not cleaned:
        return None
    for key in QUESTION_BANK:
        if cleaned.lower() == key.lower():
            return key
    return None


def get_questions_for_subject(subject: str | None = None) -> list[dict[str, Any]]:
    if subject is None:
        return [question for questions in QUESTION_BANK.values() for question in questions]

    normalized = normalize_subject(subject)
    if normalized is None:
        raise ValueError(f"Unknown subject: {subject}")
    return QUESTION_BANK[normalized]


def normalize_answer_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned.upper() if cleaned else None
    return str(value).strip().upper() if str(value).strip() else None


def evaluate_answers(subject: str, answers: list[Any]) -> dict[str, Any]:
    questions = get_questions_for_subject(subject)
    if len(answers) != len(questions):
        raise ValueError(
            f"Expected {len(questions)} answers for {subject}, received {len(answers)}."
        )

    correct_count = 0
    review: list[dict[str, Any]] = []

    for index, question in enumerate(questions):
        selected_answer = normalize_answer_value(answers[index])
        options = question["options"]
        option_keys = ["A", "B", "C", "D"]
        selected_text = None

        if selected_answer in option_keys:
            option_index = option_keys.index(selected_answer)
            if option_index < len(options):
                selected_text = options[option_index]
        elif selected_answer is not None:
            for option_index, option in enumerate(options):
                if option.lower() == selected_answer.lower():
                    selected_text = option
                    selected_answer = option_keys[option_index]
                    break

        correct_key = str(question["correct_answer"]).strip().upper()
        is_correct = selected_answer == correct_key
        if is_correct:
            correct_count += 1

        review.append(
            {
                "id": question["id"],
                "question": question["question"],
                "options": options,
                "selected_answer": selected_answer,
                "selected_value": selected_text,
                "correct_answer": correct_key,
                "is_correct": is_correct,
                "explanation": question["explanation"],
            }
        )

    total_questions = len(questions)
    percentage = round((correct_count / total_questions) * 100) if total_questions else 0
    return {
        "score": correct_count,
        "total_questions": total_questions,
        "percentage": percentage,
        "review": review,
    }
