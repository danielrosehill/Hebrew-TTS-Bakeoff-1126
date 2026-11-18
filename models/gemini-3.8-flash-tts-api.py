"""Round 1 API script: Gemini 3.8 Flash TTS. Run: with-secrets python3 models/gemini-3.8-flash-tts-api.py --ids s01"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _api_common import *

gemini_script("gemini-3.8-flash-tts", "gemini-3.8-flash-tts")
