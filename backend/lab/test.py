import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from constants.ai_prompts import ai_prompts

print(ai_prompts["gen_song_struct"])