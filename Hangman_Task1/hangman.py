import glob
import os
import random
import sqlite3
from datetime import datetime

HANGMAN_STAGES = [
    """
       +---+
       |   |
           |
           |
           |
           |
    =========
    """,
    """
       +---+
       |   |
       O   |
           |
           |
           |
    =========
    """,
    """
       +---+
       |   |
       O   |
       |   |
           |
           |
    =========
    """,
    """
       +---+
       |   |
       O   |
      /|   |
           |
           |
    =========
    """,
    """
       +---+
       |   |
       O   |
      /|\\  |
           |
           |
    =========
    """,
    """
       +---+
       |   |
       O   |
      /|\\  |
      /    |
           |
    =========
    """,
    """
       +---+
       |   |
       O   |
      /|\\  |
      / \\  |
           |
    =========
    """,
]


def init_db():
  """SQLite Database तयार करतो आणि कनेक्ट करतो."""
  script_dir = os.path.dirname(os.path.abspath(__file__))
  db_path = os.path.join(script_dir, "hangman.db")
  conn = sqlite3.connect(db_path)
  conn.execute("""
      CREATE TABLE IF NOT EXISTS game_scores (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          played_at TEXT,
          secret_word TEXT,
          result TEXT,
          mistakes INTEGER
      )
  """)
  conn.commit()
  return conn


def save_result(conn, word, result, mistakes):
  now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  conn.execute(
      "INSERT INTO game_scores (played_at, secret_word, result, mistakes) VALUES (?, ?, ?, ?)",
      (now, word, result, mistakes),
  )
  conn.commit()


def load_words():
  script_dir = os.path.dirname(os.path.abspath(__file__))
  txt_files = glob.glob(os.path.join(script_dir, "*.txt"))

  fallback_words = [
      "PYTHON",
      "HANGMAN",
      "CONSOLE",
      "PROGRAM",
      "DEVELOPER",
      "VARIABLE",
      "FUNCTION",
      "KEYBOARD",
      "NETWORK",
      "SOFTWARE",
  ]

  if not txt_files:
    return fallback_words, None

  words = []
  with open(txt_files[0], "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
      word = line.strip().upper()
      if word.isalpha() and len(word) >= 4:
        words.append(word)

  return (words, os.path.basename(txt_files[0])) if words else (fallback_words, None)


def display_board(mistakes, secret_word, correct_guesses, guessed_letters):
  print(HANGMAN_STAGES[mistakes])
  masked = " ".join(
      [ch if ch in correct_guesses else "_" for ch in secret_word]
  )
  print(f"Word:    {masked}")
  print(f"Guessed: {', '.join(sorted(guessed_letters)) or 'None'}")
  print(f"Lives:   {6 - mistakes} left\n")


def play_hangman(conn, words):
  secret_word = random.choice(words)
  correct_guesses = set()
  guessed_letters = set()
  mistakes = 0
  max_mistakes = 6

  while mistakes < max_mistakes:
    display_board(mistakes, secret_word, correct_guesses, guessed_letters)
    guess = input("Enter a letter: ").strip().upper()

    if len(guess) != 1 or not guess.isalpha():
      print("-> Invalid input! Please enter a single letter (A-Z).\n")
      continue

    if guess in guessed_letters:
      print(f"-> You already guessed '{guess}'. No life deducted!\n")
      continue

    guessed_letters.add(guess)

    if guess in secret_word:
      correct_guesses.add(guess)
      print(f"-> Correct! '{guess}' is in the word.\n")

      if all(letter in correct_guesses for letter in secret_word):
        print("=" * 40)
        print(f"  VICTORY! You guessed: {secret_word}")
        print("=" * 40)
        save_result(conn, secret_word, "VICTORY", mistakes)
        return
    else:
      mistakes += 1
      print(f"-> Wrong! '{guess}' is not in the word.\n")

  print(HANGMAN_STAGES[mistakes])
  print("=" * 40)
  print(f"  DEFEAT! The word was: {secret_word}")
  print("=" * 40)
  save_result(conn, secret_word, "DEFEAT", mistakes)


if __name__ == "__main__":
  conn = init_db()
  words, loaded_file = load_words()

  print("\n" + "=" * 45)
  print("            HANGMAN WORD GAME")
  print("=" * 45)
  print("[Database Connected] hangman.db is active.")
  if loaded_file:
    print(f"[Word List Connected] Loaded {len(words)} words from '{loaded_file}'.\n")

  while True:
    play_hangman(conn, words)
    choice = input("\nDo you want to play again? (y/n): ").strip().lower()
    if choice != "y":
      conn.close()
      print("Goodbye!")
      break