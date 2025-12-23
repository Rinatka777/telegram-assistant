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
                    "content": "You are a helpful assistant. Summarize the following document in 1 concise sentence. Focus on the main topic, dates, and money amounts."
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