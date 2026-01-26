simport streamlit as st
import speech_recognition as sr
import pygame
import asyncio
import edge_tts
import os
import time

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# --- সিম্পল সেটআপ ---
st.title("English Tutor")
st.write("Click the button and start speaking.")

# আপনার API Key এবং Mic Index
api_key = "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"
mic_index = 1  # মাইক কাজ না করলে এটি 0 বা 2 করে দেখবেন

# চ্যাট মেমোরি
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Pygame এবং AI সেটআপ
pygame.mixer.init()

# মডেল সেটআপ
try:
    model = ChatGroq(api_key=api_key, model="llama-3.1-8b-instant", temperature=0.7)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful English tutor. Keep answers short (1-2 sentences). Correct mistakes gently."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{topic}")
    ])
except Exception as e:
    st.error(f"Error setting up AI: {e}")

# --- ফাংশন ---
async def generate_voice(text):
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural", rate="+10%")
    await communicate.save("temp_audio.mp3")

def speak(text):
    try: pygame.mixer.music.unload()
    except: pass
    
    if os.path.exists("temp_audio.mp3"):
        try: os.remove("temp_audio.mp3")
        except: pass

    try:
        asyncio.run(generate_voice(text))
        
        pygame.mixer.music.load("temp_audio.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.unload()
    except Exception as e:
        st.error(f"Audio Error: {e}")

def listen():
    r = sr.Recognizer()
    with sr.Microphone(device_index=mic_index) as source:
        st.info("Listening...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=4, phrase_time_limit=5)
            return r.recognize_google(audio)
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            st.error(f"Mic Error: {e}")
            return None

# --- মেইন বাটন ---
if st.button("🎤 Start Talking"):
    user_text = listen()
    
    if user_text:
        # ১. আপনার কথা প্রিন্ট করবে
        st.write(f"**You:** {user_text}")
        
        # ২. AI উত্তর তৈরি করবে
        try:
            chain = prompt | model
            response = chain.invoke({
                "topic": user_text, 
                "chat_history": st.session_state.chat_history
            })
            ai_reply = response.content
            
            # ৩. হিস্ট্রি মনে রাখবে
            st.session_state.chat_history.append(HumanMessage(content=user_text))
            st.session_state.chat_history.append(AIMessage(content=ai_reply))
            if len(st.session_state.chat_history) > 6:
                st.session_state.chat_history = st.session_state.chat_history[-6:]
                
            # ৪. AI উত্তর প্রিন্ট করবে এবং বলবে
            st.write(f"**Tutor:** {ai_reply}")
            speak(ai_reply)
        except Exception as e:
            st.error(f"AI Error: {e}")
        
    else:
        st.warning("Could not hear anything. Try again.")

# নিচে আগের চ্যাটগুলো দেখাবে (অপশনাল)
st.write("---")
for msg in st.session_state.chat_history:
    role = "You" if isinstance(msg, HumanMessage) else "Tutor"
    st.text(f"{role}: {msg.content}")