import glob
import json
import os
import random
import re


def load_faq_dataset():
  """Automatically loads sample_faq.json (or any .json file in the script's folder)."""
  script_dir = os.path.dirname(os.path.abspath(__file__))
  default_path = os.path.join(script_dir, "sample_faq.json")
  json_files = (
      [default_path]
      if os.path.exists(default_path)
      else glob.glob(os.path.join(script_dir, "*.json"))
  )

  fallback_data = {
      "greetings": ["hello", "hi", "hey", "good morning", "good afternoon"],
      "faqs": [
          {
              "question": "What are your hours of operation?",
              "answer": (
                  "We operate Monday through Friday from 9:00 AM to 6:00 PM IST."
              ),
          },
          {
              "question": "How do I submit my internship project?",
              "answer": (
                  "You can submit your public GitHub repository link through"
                  " your Student Workspace."
              ),
          },
          {
              "question": "When will I receive my certificate?",
              "answer": (
                  "Certificates are reviewed and issued within 3-5 business"
                  " days after your code review."
              ),
          },
      ],
  }

  if not json_files:
    return fallback_data, None

  try:
    with open(json_files[0], "r", encoding="utf-8") as f:
      data = json.load(f)
      return data, os.path.basename(json_files[0])
  except (json.JSONDecodeError, OSError) as e:
    print(f"[Warning] Failed to parse JSON ({e}). Using built-in dataset.")
    return fallback_data, None


def normalize_text(text):
  """Lowercases, trims whitespace, and removes punctuation."""
  text = text.lower().strip()
  text = re.sub(r"[^\w\s]", "", text)
  return re.sub(r"\s+", " ", text)


def build_intent_rules(faq_data):
  """Maps regex patterns to answers from the loaded JSON dataset."""
  faqs = faq_data.get("faqs", [])
  rules = []

  # Keyword regex patterns mapped to FAQ entries
  keyword_patterns = [
      (
          r"\b(hours?|timing|time|open|close|operation|schedule|working)\b",
          faqs[0]["answer"] if len(faqs) > 0 else "",
      ),
      (
          r"\b(submit|submission|project|github|repo|repository|upload|link)\b",
          faqs[1]["answer"] if len(faqs) > 1 else "",
      ),
      (
          r"\b(certificate|certification|issued|receive|completion|review)\b",
          faqs[2]["answer"] if len(faqs) > 2 else "",
      ),
      (
          r"\b(help|support|commands?|options?|what can you do|menu)\b",
          (
              "I can help with: (1) Business & operating hours, (2) Internship"
              " project submission, and (3) Certificate timelines."
          ),
      ),
  ]

  for pattern, answer in keyword_patterns:
    if answer:
      rules.append((re.compile(pattern, re.IGNORECASE), answer))

  # Dynamically include any extra FAQs if added to sample_faq.json later
  stop_words = {
      "what",
      "are",
      "your",
      "of",
      "how",
      "do",
      "i",
      "my",
      "when",
      "will",
      "the",
      "is",
      "to",
      "a",
      "in",
  }
  for extra_faq in faqs[3:]:
    q_words = [
        w
        for w in normalize_text(extra_faq.get("question", "")).split()
        if w not in stop_words and len(w) > 2
    ]
    if q_words:
      dynamic_pattern = r"\b(" + "|".join(map(re.escape, q_words)) + r")\b"
      rules.append(
          (re.compile(dynamic_pattern, re.IGNORECASE), extra_faq.get("answer", ""))
      )

  return rules


def run_chatbot():
  faq_data, loaded_file = load_faq_dataset()
  greetings = faq_data.get("greetings", ["hello", "hi", "hey"])
  greeting_pattern = re.compile(
      r"\b(" + "|".join(map(re.escape, greetings)) + r")\b", re.IGNORECASE
  )
  exit_pattern = re.compile(
      r"\b(bye|exit|quit|goodbye|see ya)\b", re.IGNORECASE
  )
  intent_rules = build_intent_rules(faq_data)

  # State management: GREETING -> ACTIVE -> EXIT
  state = "GREETING"

  print("=" * 62)
  print("         INTERACTIVE SUPPORT ASSISTANT (CHATBOT)")
  print("=" * 62)
  if loaded_file:
    print(f"[Dataset Connected] Loaded FAQs from '{loaded_file}'.")
  print("Type 'bye', 'exit', or 'quit' anytime to end the chat.\n")
  print("Bot: Hello! Welcome to Student Support. How can I assist you today?")

  while state != "EXIT":
    try:
      user_raw = input("\nYou: ").strip()
    except (KeyboardInterrupt, EOFError):
      print("\nBot: Session interrupted. Goodbye!")
      break

    if not user_raw:
      print("Bot: Please type a message or question so I can help you.")
      continue

    cleaned = normalize_text(user_raw)

    # 1. Check Exit Intent
    if exit_pattern.search(cleaned):
      state = "EXIT"
      print("Bot: Thank you for reaching out! Have a great day. Goodbye!")
      break

    responses = []

    # 2. Check Greeting Intent
    if greeting_pattern.search(cleaned):
      state = "ACTIVE"
      responses.append(
          f"{random.choice(greetings).capitalize()}! Hope you're doing well."
      )

    # 3. Check Multi-Intent FAQ Rules
    for pattern, answer in intent_rules:
      if pattern.search(cleaned) and answer not in responses:
        state = "ACTIVE"
        responses.append(answer)

    # 4. Output Contextual Response or Graceful Fallback
    if responses:
      print("Bot: " + " ".join(responses))
    else:
      print(
          "Bot: I'm sorry, I didn't quite catch that. You can ask me about"
          " operating hours, project submission, or certificates."
      )


if __name__ == "__main__":
  run_chatbot()