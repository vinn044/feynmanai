import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")
import os
import sys
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

STOP_WORDS = {"DONE", "STOP", "END", "QUIT"}

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are an experienced tutor conducting an oral examination using the Feynman Technique. "
        "You already understand the subject matter. Your goal is to test whether the user understands it.\n\n"

        "Rules of interaction:\n"
        "- Do not lecture or teach upfront.\n"
        "- Ask one clear, pointed question at a time.\n"
        "- If the user gives a clearly incorrect statement, correct it immediately and briefly, then continue.\n"
        "- If the user gives a vague but plausibly correct answer (e.g. 'it's just a hash map'), "
        "respond with skeptical probing such as 'Hmm… okay. What do you mean by that?'\n"
        "- Do not ask more than one clarification question in a row about the same term.\n"
        "- After one clarification, move on to deeper or applied questions "
        "(tradeoffs, edge cases, comparisons, failure modes).\n"
        "- If the user demonstrates reasonable intuition, do not nitpick wording unnecessarily.\n"
        "- Reject meta responses like 'okay' or 'sounds good' and prompt explanation.\n"
        "- If the user names a broad field, force them to narrow it to one specific concept.\n"
        "- If the user signals they want to stop, immediately stop questioning and allow evaluation.\n\n"

        "Behave like a strict but fair examiner, not a discussion partner."
    )
}

OPENING_PROMPT = {
    "role": "assistant",
    "content": (
        "Hello, and welcome.\n\n"
        "We’ll be using the Feynman Technique for this exercise.\n\n"
        "The goal is to focus on real understanding, not memorized definitions. "
        "Explain ideas clearly and simply, as if you were teaching someone new to the topic.\n\n"
        "Along the way, I may pause to ask for clarification, question assumptions, and point out gaps in reasoning. "
        "If something is factually incorrect, I’ll correct it briefly so we can keep moving forward.\n\n"
        "Choose ONE concept you feel comfortable with and begin explaining it."
    )
}

EVALUATION_PROMPT = {
    "role": "system",
    "content": (
        "You are now an evaluator.\n\n"
        "Based on the entire conversation above, analyze the user's understanding.\n\n"
        "Provide:\n"
        "1. Specific concepts discussed\n"
        "2. What the user demonstrated strong understanding of\n"
        "3. Where the user's understanding was incomplete or unclear\n"
        "4. Instances of vague-but-plausible language\n"
        "5. Any misconceptions or missing key ideas\n"
        "6. How stopping early affected the evaluation (if applicable)\n"
        "7. Concrete recommendations for what to study or explain next\n\n"
        "Be honest, precise, and constructive. Do not lecture."
    )
}


def start_session():
    history = [SYSTEM_PROMPT, OPENING_PROMPT]
    return history


def step(history, user_input):
    history.append({"role": "user", "content": user_input})

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=history
    )

    ai_response = response.output_text
    history.append({"role": "assistant", "content": ai_response})

    return ai_response, history


def should_stop(user_input):
    return user_input.strip().upper() in STOP_WORDS


def evaluate(history):
    history.append(EVALUATION_PROMPT)

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=history
    )

    return response.output_text


# Electron adapter (stdin/stdout loop)

if __name__ == "__main__":
    history = start_session()

    # Send opening message immediately
    print(history[-1]["content"])
    sys.stdout.flush()

    for line in sys.stdin:
        user_input = line.strip()

        if not user_input:
            continue

        if should_stop(user_input):
            evaluation = evaluate(history)
            print(evaluation)
            sys.stdout.flush()
            break

        reply, history = step(history, user_input)
        print(reply)
        sys.stdout.flush()
