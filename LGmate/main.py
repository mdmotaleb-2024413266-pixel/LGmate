import asyncio
import base64
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import edge_tts
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
import os
from dotenv import load_dotenv
app = FastAPI()
# .env ফাইল থেকে ভেরিয়েবলগুলো লোড করার জন্য
load_dotenv()

# এখন সিস্টেম এনভায়রনমেন্ট থেকে কি-টি সংগ্রহ করা হচ্ছে
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# চেক করার জন্য (অপশনাল কিন্তু নিরাপদ)
if GROQ_API_KEY is None:
    print("Error: GROQ_API_KEY পাওয়া যায়নি! .env ফাইলটি চেক করুন।")
else:
    print("API Key সফলভাবে লোড হয়েছে।")
# CORS সেটআপ (যাতে ব্রাউজার থেকে রিকোয়েস্ট ব্লক না হয়)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- কনফিগারেশন ---

model = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0.7
)

# আপনার অরিজিনাল প্রম্পটটি এখানে সঠিকভাবে সেট করা হয়েছে
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a friendly and supportive English tutor acting as a best friend. 
    The user is speaking to you to practice and improve their English.

    Your responsibilities are:
    1. **Conversational Partner:** Chat naturally about the topic the user raises. Be encouraging and funny.
    2. **Corrections:** If the user makes a grammar or vocabulary mistake, gently correct them at the end of your response.
    3. **Suggestions:** Suggest a better or more "native-speaker" like way to phrase their sentence if possible.
    4. **Tone:** Always remain kind, patient, and friendly. Do not lecture the user.
    
    IMPORTANT: Since this is a voice chat, keep your responses concise (maximum 2-3 sentences).
    """),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{topic}")
])

chat_history = []
EN_VOICE = "en-US-AriaNeural"

@app.post("/chat")
async def chat_endpoint(request: Request):
    global chat_history
    try:
        data = await request.json()
        user_input = data.get("text", "")

        # AI ব্রেইন প্রসেসিং
        chain = prompt | model
        response = chain.invoke({
            "topic": user_input, 
            "chat_history": chat_history
        })
        ai_reply = response.content

        # হিস্টোরি ম্যানেজমেন্ট
        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=ai_reply))
        if len(chat_history) > 6:
            chat_history = chat_history[-6:]

        # টেক্সট টু স্পিচ (TTS)
        communicate = edge_tts.Communicate(ai_reply, EN_VOICE, rate="+10%")
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        audio_base64 = base64.b64encode(audio_data).decode('utf-8')

        return {
            "reply": ai_reply,
            "audio": audio_base64
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}
if __name__ == "__main__":
    import uvicorn
    # Render বা অন্য হোস্টিং সার্ভার অটোমেটিক PORT অ্যাসাইন করে দেয়
    port = int(os.environ.get("PORT", 8000)) 
    uvicorn.run(app, host="0.0.0.0", port=port)










