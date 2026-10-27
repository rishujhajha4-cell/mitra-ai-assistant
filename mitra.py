import datetime
import os
import re
import subprocess
import time
import requests
import speech_recognition as sr

recognizer = sr.Recognizer()

ASSISTANT_NAME = "Mitra"
OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "llama3"

SYSTEM_PROMPT = """
You are Mitra, an encouraging, friendly AI learning mentor for children aged 8 and older.
Guidelines:
1. Use simple, engaging words suitable for an 8-to-12-year-old child.
2. Keep spoken replies brief (2 to 4 sentences maximum) so they are easy to listen to.
3. Never use markdown formatting like asterisks, bullet points, numbers, or symbols. 
4. Always speak directly in plain, friendly English sentences.
"""

def clean_speech_text(text: str) -> str:
    text = re.sub(r"[*_#`~>\[\]\(\)\{\}]", " ", text)
    text = text.replace('"', "").replace("'", "").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def speak(text: str):
    clean = clean_speech_text(text)
    print(f"\n{ASSISTANT_NAME}: {clean}\n")
    subprocess.run(["say", "-r", "165", clean])
    time.sleep(0.5)

def ai_response(prompt: str, task_context: str = "") -> str:
    full_prompt = f"{SYSTEM_PROMPT}\nContext: {task_context}\nPrompt: {prompt}\nMitra:"
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 100
        }
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json().get("response", "").strip()
            return result or "ERROR_EMPTY"
        else:
            return "ERROR_API"
    except Exception as e:
        return f"ERROR: {e}"

def listen(timeout_sec: int = 8, phrase_limit_sec: int = 6) -> str:
    try:
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=timeout_sec, phrase_time_limit=phrase_limit_sec)
        text = recognizer.recognize_google(audio).lower()
        print(f"Child: {text}")
        return text
    except (sr.WaitTimeoutError, sr.UnknownValueError):
        return ""
    except Exception:
        return ""

def open_url(url: str):
    subprocess.run(["open", url])

def run_interactive_quiz():
    speak("Let us test your brain power! Thinking of a question for you.")
    question_prompt = (
        "Ask a single multiple-choice question for an 8-year-old child about animals, science, or planets. "
        "State options A, B, and C clearly in words. Do not give the answer yet."
    )
    quiz_question = ai_response(question_prompt, task_context="Interactive Quiz Generator")
    if quiz_question.startswith("ERROR"):
        speak("I had a little trouble creating the question. Let us try something else!")
        return

    speak(quiz_question)
    speak("What is your answer?")
    child_answer = listen(timeout_sec=9, phrase_limit_sec=6)
    if not child_answer:
        speak("No problem! We can try another quiz next time.")
        return

    evaluation_prompt = (
        f"The question was: '{quiz_question}'. "
        f"The child answered: '{child_answer}'. "
        f"Tell them kindly if they are right or wrong, provide the correct answer, "
        f"and say one encouraging sentence."
    )
    feedback = ai_response(evaluation_prompt, task_context="Quiz Answer Evaluation")
    if not feedback.startswith("ERROR"):
        speak(feedback)
    else:
        speak("Great attempt! Keep practicing and learning.")

def tell_story(cmd: str):
    topic = cmd.replace("tell me a story", "").replace("tell a story", "").replace("story about", "").replace("story", "").strip()
    if not topic or len(topic) < 3:
        topic = "friendship and curiosity"
    speak(f"Here is a short story about {topic}.")
    story_prompt = (
        f"Tell an engaging moral story for an 8-year-old child focusing on {topic}. "
        "Include a positive lesson at the end. Strictly keep it under 4 spoken sentences."
    )
    story = ai_response(story_prompt, task_context="Storytelling with Moral Values")
    if not story.startswith("ERROR"):
        speak(story)
    else:
        speak("I am having a little trouble thinking of a story right now. Let us try again!")

def word_of_the_day():
    speak("Here is your new word for today.")
    vocab_prompt = (
        "Pick one inspiring vocabulary word for an 8-year-old child like curious, brave, or resilient. "
        "Explain what it means simply and give one cheerful example sentence."
    )
    vocab = ai_response(vocab_prompt, task_context="Vocabulary Builder")
    if not vocab.startswith("ERROR"):
        speak(vocab)
    else:
        speak("Todays word is Curious: wanting to discover and learn wonderful new things!")

def process_command(cmd: str) -> bool:
    if "quiz" in cmd or "test me" in cmd or "riddle" in cmd:
        run_interactive_quiz()
    elif "story" in cmd:
        tell_story(cmd)
    elif "new word" in cmd or "word of the day" in cmd or "vocabulary" in cmd:
        word_of_the_day()
    elif "math" in cmd and "open" in cmd:
        speak("Opening Khan Academy Math for practice.")
        open_url("https://www.khanacademy.org/math")
    elif "books" in cmd or "read" in cmd or "library" in cmd:
        speak("Opening StoryWeaver for free books.")
        open_url("https://storyweaver.org.in")
    elif "time" in cmd:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"It is {current_time}. Keep up the great work today!")
    elif "exit" in cmd or "stop" in cmd or "bye" in cmd or "goodbye" in cmd:
        speak("Awesome job learning today! Keep asking questions. Goodbye!")
        return False
    else:
        speak("Let me think about that.")
        explanation_prompt = f"Explain this simply in 2 sentences for an 8-year-old child: {cmd}"
        explanation = ai_response(explanation_prompt, task_context="Child Doubt Solving")
        if not explanation.startswith("ERROR"):
            speak(explanation)
        else:
            speak("I could not get an answer for that right now. Let us ask something else!")
    return True

if __name__ == "__main__":
    print("Checking Ollama connection...")
    test_ping = ai_response("say ready in one word", task_context="init")
    if test_ping.startswith("ERROR"):
        print("Warning: Ollama is not responding yet. Ensure ollama serve is running.")
    else:
        print("Model is warm and ready.")

    speak(f"Hello! I am {ASSISTANT_NAME}, your study companion. Say {ASSISTANT_NAME} to wake me up.")
    while True:
        text = listen(timeout_sec=7, phrase_limit_sec=5)
        if any(wake_word in text for wake_word in [ASSISTANT_NAME.lower(), "mitra", "wake up"]):
            speak("I am here! Would you like a story, a quiz, or a new word today?")
            user_command = listen(timeout_sec=9, phrase_limit_sec=6)
            if user_command:
                should_continue = process_command(user_command)
                if not should_continue:
                    break
