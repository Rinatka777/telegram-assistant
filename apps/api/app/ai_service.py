import os
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_text(text: str) -> str:
    if not text:
        return "No text found."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful and caring assistant. If the document is uploaded - summarize it in 1 concise sentence. Focus on the main topic, dates, and money amounts. If the user ask questions- ask politely and friendly-you can use smiles"
                },
                {"role": "user", "content": f"Here is the text:\n\n{text}"}
            ],
            max_tokens=150,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI Error: {e}")
        return "Summary unavailable."

def answer_user_question(context:str, question:str) -> str:
    if not context or not question:
        return "No context or question found."
    try:
        response = client.chat.completions.create(
            model = "gpt-4o-mini",
            messages = [
                {"role": "system", "content": (
                    "You are a helpful assistant. "
                    "If Context is provided, prioritize it to answer the question. "
                    "If the Context is missing or irrelevant, answer from your own general knowledge. "
                    "Be polite and concise."
                )},
                {"role": "user", "content": f"Context: {context}\nQuestion: {question}"}
            ],
            max_tokens=150,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI Chat Error: {e}")
        return "I'm having trouble thinking right now (AI Error)."

def transcribe_audio(file_path: str) -> str:
    if not os.path.exists(file_path):
        return "Voice file not found."

    try:
        audio_file = open(file_path, "rb")
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return transcript.text
    except Exception as e:
        print(f"Whisper Error: {e}")
        return "Error transcribing audio."