import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")

import os
import json
from openai import OpenAI
from io import BytesIO
import numpy as np
import wave

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

STOP_WORDS = {"DONE", "STOP", "END", "QUIT"}

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are an experienced tutor conducting an oral examination using the Feynman Technique. "
        "You already understand the subject matter. Your goal is to test whether the user understands it.\n\n"
        "Keep responses brief (1-2 sentences max). Be conversational and engaging."
    )
}

OPENING_PROMPT = {
    "role": "assistant",
    "content": "Hello! Tell me a concept you'd like to explain."
}

history = []
voice_session_active = False
audio_buffer = []
silence_counter = 0

def start_session():
    global history
    history = [SYSTEM_PROMPT, OPENING_PROMPT]
    return history

def step(hist, user_input):
    hist.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=hist
    )

    ai_response = response.choices[0].message.content
    hist.append({"role": "assistant", "content": ai_response})

    return ai_response, hist

def should_stop(user_input):
    """Check if user wants to stop the session"""
    return user_input.strip().upper() in STOP_WORDS

def evaluate(history):
    """Evaluate the session and provide feedback"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert tutor evaluator. Analyze the conversation and provide constructive feedback on the student's understanding."},
            {"role": "user", "content": f"Here's a tutoring session:\n\n{json.dumps(history)}\n\nPlease evaluate the student's understanding and provide feedback."}
        ]
    )
    return response.choices[0].message.content

def transcribe_audio(audio_data):
    """Convert audio data to text using Whisper"""
    try:
        if not audio_data or len(audio_data) < 50:
            return None
            
        audio_array = np.array(audio_data, dtype=np.float32)
        int_data = np.int16(audio_array * 32767)
        
        wav_data = BytesIO()
        sample_rate = 24000
        with wave.open(wav_data, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(int_data.tobytes())
        
        wav_data.seek(0)
        
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.wav", wav_data, "audio/wav")
        )
        
        text = transcript.text.strip()
        return text if text else None
    except Exception as e:
        print(f"Error transcribing: {e}", file=sys.stderr)
        sys.stderr.flush()
        return None

def text_to_speech(text):
    """Convert text to speech using OpenAI TTS"""
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
            response_format="pcm"
        )
        
        audio_bytes = response.content
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        return audio_array.tolist()
    except Exception as e:
        print(f"Error in TTS: {e}", file=sys.stderr)
        sys.stderr.flush()
        return None

def detect_speech_activity(audio_data):
    """Detect if there's speech in audio chunk"""
    if not audio_data:
        return False
    
    audio_array = np.array(audio_data, dtype=np.float32)
    rms = np.sqrt(np.mean(audio_array ** 2))
    
    return rms > 0.01

def main():
    global voice_session_active, audio_buffer, history, silence_counter
    
    start_session()
    opening = history[-1]["content"]
    print(json.dumps({"type": "text", "content": opening}))
    sys.stdout.flush()

    while True:
        try:
            line = sys.stdin.readline().strip()
            if not line:
                continue

            message = json.loads(line)
            msg_type = message.get("type")

            if msg_type == "text":
                content = message.get("content", "")
                if content:
                    reply = step(content)
                    print(json.dumps({"type": "text", "content": reply}))
                    sys.stdout.flush()

            elif msg_type == "voice_start":
                voice_session_active = True
                audio_buffer = []
                silence_counter = 0
                
                # Send opening greeting via speech
                audio_response = text_to_speech(opening)
                if audio_response:
                    print(f"AUDIO:{json.dumps(audio_response)}")
                    sys.stdout.flush()
                
                print(json.dumps({"type": "text", "content": "Listening..."}))
                sys.stdout.flush()

            elif msg_type == "voice_stop":
                voice_session_active = False
                audio_buffer = []
                silence_counter = 0
                print(json.dumps({"type": "text", "content": "Voice session ended"}))
                sys.stdout.flush()

            elif msg_type == "audio" and voice_session_active:
                audio_data = message.get("data", [])
                if audio_data:
                    has_speech = detect_speech_activity(audio_data)
                    audio_buffer.extend(audio_data)
                    
                    # Count silence frames
                    if not has_speech:
                        silence_counter += 1
                    else:
                        silence_counter = 0
                    
                    # Process audio when we have enough accumulated
                    # OR when user has been silent after speaking
                    should_process = False
                    
                    if len(audio_buffer) > 6000 and silence_counter > 10:
                        # Has audio AND has been silent for ~0.5 seconds
                        should_process = True
                    
                    if should_process:
                        transcribed = transcribe_audio(audio_buffer)
                        
                        if transcribed and len(transcribed) > 2:
                            print(json.dumps({"type": "text", "content": f"You: {transcribed}"}))
                            sys.stdout.flush()
                            
                            # Get AI response
                            reply = step(transcribed)
                            
                            print(json.dumps({"type": "text", "content": f"AI: {reply}"}))
                            sys.stdout.flush()
                            
                            # Convert to speech
                            audio_response = text_to_speech(reply)
                            
                            if audio_response:
                                print(f"AUDIO:{json.dumps(audio_response)}")
                                sys.stdout.flush()
                        
                        audio_buffer = []
                        silence_counter = 0

        except json.JSONDecodeError:
            continue
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.stderr.flush()

if __name__ == "__main__":
    main()