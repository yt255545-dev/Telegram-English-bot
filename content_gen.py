"""
Calls Gemini to generate an advanced notes explanation + 5 hard MCQs.
"""
import json
import re
import random
import google.generativeai as genai
from config import GEMINI_API_KEY, TOPIC_POOL

genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-1.5-pro"  # change to whatever Gemini text model is available on your account

PROMPT_TEMPLATE = """You are an expert English grammar teacher writing content for an advanced
Telegram learning channel. Everything must be in English.

Topic: {topic}

Write:
1. "notes": A concise (60-100 words) advanced-level explanation of this topic, written like
   a well-organized notebook page. Include 2-4 short bullet points. Mark the single MOST
   important rule or exception by wrapping it in double asterisks, e.g. **like this**.
2. "questions": Exactly 5 VERY DIFFICULT multiple-choice questions testing deep/advanced
   understanding of "{topic}" (edge cases, exceptions, commonly confused forms - not basic
   recall). Each question has exactly 4 options and exactly one correct option.

Return ONLY valid JSON, no markdown fences, no commentary, in this exact shape:
{{
  "notes": "string",
  "questions": [
    {{
      "question": "string",
      "options": ["...", "...", "...", "..."],
      "correct_index": 0
    }}
  ]
}}
"""


def _clean_json(raw_text):
    cleaned = re.sub(r"^```(json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


def generate_quiz_content(topic=None):
    topic = topic or random.choice(TOPIC_POOL)
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(PROMPT_TEMPLATE.format(topic=topic))
    data = _clean_json(response.text)

    assert "notes" in data and "questions" in data, "Malformed Gemini response"
    assert len(data["questions"]) == 5, "Expected exactly 5 questions"
    for q in data["questions"]:
        assert len(q["options"]) == 4, "Each question needs exactly 4 options"
        assert 0 <= q["correct_index"] <= 3

    data["topic"] = topic
    return data
