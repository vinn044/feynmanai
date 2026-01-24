import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


STOP_WORDS = {"DONE", "STOP", "END", "QUIT"}

system_prompt = {
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

history = [system_prompt]

opening_prompt = {
    "role": "assistant",
    "content": (
        "I will act as an examiner using the Feynman Technique.\n\n"
        "Your task is to demonstrate real understanding, not memorized definitions. "
        "Explain ideas simply and precisely, as if teaching a beginner.\n\n"
        "I will challenge vague statements, probe assumptions, and interrupt unclear reasoning. "
        "If something you say is factually wrong, I will correct it briefly and move on.\n\n"
        "Choose ONE specific concept you believe you understand well and begin explaining it."
    )
}

history.append(opening_prompt)
print("\nTutor:", opening_prompt["content"])

# ===== Examination Loop =====

while True:
    user_input = input("\nYou: ")

    if user_input.strip().upper() in STOP_WORDS:
        break

    history.append({"role": "user", "content": user_input})

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=history
    )

    ai_response = response.output_text
    print(f"\nTutor: {ai_response}")

    history.append({"role": "assistant", "content": ai_response})


# ===== End-of-Conversation Evaluation =====

evaluation_prompt = {
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

history.append(evaluation_prompt)

final_response = client.responses.create(
    model="gpt-4.1-mini",
    input=history
)

print("\n===== END OF SESSION ANALYSIS =====\n")
print(final_response.output_text)
