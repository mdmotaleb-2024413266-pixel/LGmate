import streamlit as st
import streamlit.components.v1 as components
import time
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

my_api_key = "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"


class VoiceAssistant:
    def __init__(self):
        # সেশন স্টেটে মেমোরি ধরে রাখা
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "last_speech" not in st.session_state:
            st.session_state.last_speech = ""

    def render_js_engine(self):
        """ব্রাউজারে ভয়েস ডিটেকশন এবং লুপ চালানোর ইঞ্জিন"""
        js_code = """
        <div id="status" style="padding:15px; border-radius:10px; background:#f4f4f4; text-align:center; border:1px solid #ddd;">
            <p id="msg" style="font-weight:bold; color:#333;">System Ready</p>
            <button id="btn" onclick="startLoop()" style="padding:10px 20px; background:#ff4b4b; color:white; border:none; border-radius:5px; cursor:pointer;">Activate Loop 🔄</button>
        </div>

        <script>
            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'en-US';
            recognition.continuous = false;
            let isLooping = false;

            function startLoop() {
                isLooping = true;
                document.getElementById('btn').style.display = 'none';
                listen();
            }

            function listen() {
                if(!isLooping) return;
                recognition.start();
                document.getElementById('msg').innerText = "🔴 Listening...";
            }

            recognition.onresult = (event) => {
                const text = event.results[0][0].transcript;
                document.getElementById('msg').innerText = "✅ Captured: " + text;
                
                // পাইথনে ডাটা পাঠানো
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: text}, '*');
                
                // কথাটি বাজিয়ে শোনানো (Loopback)
                const speech = new SpeechSynthesisUtterance(text);
                speech.onend = () => { 
                    setTimeout(listen, 500); // বলা শেষ হলে আবার শোনা শুরু
                };
                window.speechSynthesis.speak(speech);
            };

            recognition.onend = () => {
                // সাইলেন্স বা এরর হলে অটোমেটিক রিস্টার্ট
                if(document.getElementById('msg').innerText === "🔴 Listening...") {
                    listen();
                }
            };
        </script>
        """
        return components.html(js_code, height=150)

    def process_and_display(self, text):
        """ইউজার যা বলেছে তা প্রসেস করা"""
        if text and text != st.session_state.last_speech:
            st.session_state.last_speech = text
            st.session_state.chat_history.append(f"You: {text}")
            return True
        return False

# --- অ্যাপ রান করা ---
bot = VoiceAssistant()
captured_text = bot.render_js_engine()

# আউটপুট ডিসপ্লে
st.subheader("Live Interaction Log")
chat_placeholder = st.empty()

if bot.process_and_display(captured_text):
    with chat_placeholder.container():
        for msg in reversed(st.session_state.chat_history):
            st.write(msg)