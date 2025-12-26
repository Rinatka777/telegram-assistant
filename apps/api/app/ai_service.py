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
                {"role": "system", "content": "You are a helpful and caring assistant. If the document is uploaded - summarize it in 1 concise sentence. Focus on the main topic, dates, and money amounts. If the user ask questions- ask politely and friendly-you can use smiles"},
                {"role": "user", "content": f"Context: {context}\nQuestion: {question}"}
            ],
            max_tokens=150,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI Chat Error: {e}")
        return "I'm having trouble thinking right now (AI Error)."
