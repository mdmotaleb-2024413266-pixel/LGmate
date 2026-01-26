import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import torch
import numpy as np

st.title("AI Powered Voice Detector (Silero)")

# ১. Silero VAD মডেল লোড করা (এটি মাত্র ২-৩ মেগাবাইট)
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=False)

(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

class AudioProcessor:
    def recv(self, frame):
        # অডিওকে ফ্লোট টেন্সরে রূপান্তর
        audio_data = frame.to_ndarray().astype(np.float32) / 32768.0
        audio_tensor = torch.from_numpy(audio_data)

        # ২. AI চেক করছে এটা কি মানুষের গলা?
        # ০.৫ এর বেশি মানেই মানুষ কথা বলছে
        speech_prob = model(audio_tensor, 16000).item()

        if speech_prob > 0.5:
            print(f"🔥 AI ডিটেকশন: কথা বলছেন (Confidence: {speech_prob:.2f})")
        else:
            print("... নীরবতা ...")

        return frame

webrtc_streamer(
    key="silero-vad",
    mode=WebRtcMode.SENDONLY,
    media_stream_constraints={
        "video": False,
        "audio": {"sampleRate": 16000}
    },
    audio_processor_factory=AudioProcessor,
)