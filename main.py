import tkinter as tk
from tkinter import filedialog
from pdfminer.high_level import extract_text
import re
import pygame
from mutagen.mp3 import MP3
import threading
import time

# 1. File selection dialog
root = tk.Tk()
root.withdraw()  # Hide while asking for filenames

pdf_file = filedialog.askopenfilename(
    title="Select PDF File",
    filetypes=[("PDF files", "*.pdf")]
)
audio_file = filedialog.askopenfilename(
    title="Select Audio File",
    filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
)

root.deiconify()  # Show GUI now

# 2. Extract and process PDF text
text = extract_text(pdf_file)
text = re.sub(r'\b(\w) (\w)\b', r'\1\2', text)
words = text.strip().split()
cleaned_words = []
for w in words:
    if len(w) == 1 and w.isalpha():
        if cleaned_words:
            cleaned_words[-1] += w
        else:
            cleaned_words.append(w)
    else:
        cleaned_words.append(w)
words = cleaned_words

# 3. Audio file analysis
audio = MP3(audio_file)
audio_duration = audio.info.length
delay_per_word = audio_duration / len(words)

# 4. Audio playback function
def play_audio():
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()
    print("Playing audio...")

audio_thread = threading.Thread(target=play_audio)
audio_thread.start()

# 5. Set up main Tkinter UI (ONE root, ONE text_widget)
root.title("PDF Audio Synced Reader")
root.geometry("900x700")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(fill="both", expand=True)
scrollbar = tk.Scrollbar(frame)
scrollbar.pack(side="right", fill="y")

text_widget = tk.Text(
    frame,
    wrap="word",
    font=("Calibri", 15),
    yscrollcommand=scrollbar.set,
    bg="#f8f8f8",
    padx=12,
    pady=12
)
text_widget.pack(expand=1, fill="both")
scrollbar.config(command=text_widget.yview)

text_widget.insert("1.0", text)
text_widget.tag_configure("highlight", background="yellow")

# --- Build indices for clean word-by-word highlighting ---
start_indices = []
end_indices = []
full_text = text_widget.get("1.0", "end-1c")
idx = 0
for word in words:
    while idx < len(full_text) and full_text[idx].isspace():
        idx += 1
    start = idx
    end = idx + len(word)
    start_indices.append(start)
    end_indices.append(end)
    idx = end

# --- Ultra-smooth (timer-based) highlight function ---
import time
highlight_start_time = None
def highlight_words():
    global highlight_start_time
    if highlight_start_time is None:
        highlight_start_time = time.time()
    elapsed = time.time() - highlight_start_time
    idx = int(elapsed / delay_per_word)
    if idx >= len(start_indices):
        return
    text_widget.tag_remove("highlight", "1.0", "end")
    start_index = f"1.0+{start_indices[idx]}c"
    end_index = f"1.0+{end_indices[idx]}c"
    text_widget.tag_add("highlight", start_index, end_index)
    text_widget.see(start_index)
    root.after(20, highlight_words)   # ~50 FPS for smooth visual update

# --- Start highlighting with minimal lag ---
highlight_start_time = None
root.after(20, highlight_words)

root.mainloop()
