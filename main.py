from engine import start_session, step, should_stop, evaluate

history = start_session()

print("\nTutor:", history[-1]["content"])

while True:
    user_input = input("\nYou: ")

    if should_stop(user_input):
        break

    reply, history = step(history, user_input)
    print("\nTutor:", reply)

print("\n===== END OF SESSION ANALYSIS =====\n")
print(evaluate(history))
