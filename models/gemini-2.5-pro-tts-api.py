"""Round 1 API script: Gemini 2.5 Pro TTS. Run: with-secrets python3 models/gemini-2.5-pro-tts-api.py --ids s01"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _api_common import *

gemini_script("gemini-2.5-pro-tts", "gemini-2.5-pro-preview-tts")
