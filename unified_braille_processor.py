import speech_recognition as sr
import time
import re
import pandas as pd
from jiwer import wer
import os

# --- CORE BRAILLE MODEL & UTILITIES (Same as before) ---
BRAILLE_MAP = {
    "the": "⠮", "and": "⠯", "for": "⠿", "with": "⠾", "of": "⠷",
    "is": "⠊⠎", "to": "⠞⠕", "it": "⠊⠞", "that": "⠹", "was": "⠺⠁⠎",
    "will": "⠺⠇", "can": "⠉⠁⠝", "you": "⠽",
    "a": "⠁", "b": "⠃", "c": "⠉", "d": "⠙", "e": "⠑", 
    "f": "⠋", "g": "⠛", "h": "⠓", "i": "⠊", "j": "⠚", 
    "l": "⠇", "m": "⠍", "n": "⠝", "o": "⠕", "p": "⠏", "q": "⠟", "r": "⠗", "s": "⠎", "t": "⠞",
    "u": "⠥", "v": "⠧", "w": "⠺", "x": "⠭", "y": "⠽", "z": "⠵",
    " ": "⠀", ",": "⠄", ".": "⠲", "?": "⠹", "!": "⠖",
}

def translate_to_simplified_braille(text):
    """Python-Native Simplified Grade 2 Translation."""
    tokens = re.findall(r"[\w']+|[.,!?]", text.lower())
    braille_output = []
    for token in tokens:
        if token in BRAILLE_MAP:
            braille_output.append(BRAILLE_MAP[token])
        else:
            braille_word = "".join([BRAILLE_MAP.get(char, char) for char in token])
            braille_output.append(braille_word)
    return "⠀".join(braille_output)

def calculate_contraction_ratio(english_text, braille_output):
    """Calculates Braille cells / English characters (excluding spaces)."""
    # Count only alphabetic characters
    english_chars = len(re.sub(r'[^a-zA-Z]', '', english_text)) 
    braille_cells = len(braille_output)
    ratio = braille_cells / english_chars if english_chars > 0 else 0
    return english_chars, braille_cells, ratio

# --- INPUT MODULES ---

def process_text_file(file_path):
    """Module to read text from a file (simulating SMS/Chat)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
            return text, "TEXT_FILE", 0.0, None # Source, Latency, Ground Truth
    except FileNotFoundError:
        return f"Error: File not found at {file_path}", "Error", 0.0, None

def process_audio_file(file_path):
    """Module to transcribe audio from a file (simulating Voice Message)."""
    r = sr.Recognizer()
    
    if not os.path.exists(file_path):
        return f"Error: Audio file not found at {file_path}", "Error", 0.0, None
        
    try:
        with sr.AudioFile(file_path) as source:
            audio = r.record(source) 
            start_time = time.time()
            transcribed_text = r.recognize_google(audio)
            latency = time.time() - start_time
            return transcribed_text.strip(), "AUDIO_FILE", latency, input("Enter the EXACT spoken phrase (Ground Truth) for WER calculation: ")
            
    except sr.UnknownValueError:
        return "Error: Could not understand audio.", "Error", 0.0, None
    except sr.RequestError as e:
        return f"Error: Google API failed; check internet. {e}", "Error", 0.0, None
    except Exception as e:
        return f"An unexpected audio error occurred: {e}", "Error", 0.0, None

# --- MAIN DEMO LOOP ---

def run_unified_demo():
    print("--- Unified Braille Translation Demo (File-Based) ---")
    
    while True:
        choice = input("\nEnter input type ('text' or 'audio') or 'quit': ").lower().strip()
        
        if choice == 'quit':
            break
        
        if choice not in ['text', 'audio']:
            print("Invalid choice. Please enter 'text', 'audio', or 'quit'.")
            continue

        file_path = input(f"Enter the path to the {choice} file: ")
        
        # 1. Process Input File (Source Agnostic)
        if choice == 'text':
            text, source, latency, ground_truth = process_text_file(file_path)
        else: # choice == 'audio'
            text, source, latency, ground_truth = process_audio_file(file_path)
        
        if source == "Error" or "Error:" in text:
            print(text)
            continue
            
        # 2. Translate and Analyze
        start_process_time = time.time()
        
        # Simple Capitalization Rule
        display_text = text
        if display_text and display_text[0].isupper():
            text = "⠠" + text 
        
        braille_output = translate_to_simplified_braille(text)
        translation_time = time.time() - start_process_time
        
        # 3. Calculate Metrics
        english_chars, braille_cells, ratio = calculate_contraction_ratio(display_text, braille_output)
        
        # WER is only calculated for audio input where ground truth is provided
        calculated_wer = wer(ground_truth.lower(), display_text.lower()) if ground_truth else "N/A"
        
        # 4. Display Results
        print("\n" + "="*50)
        print(f"| INPUT SOURCE: {source} | TOTAL LATENCY: {latency + translation_time:.3f}s |")
        print("="*50)
        print(f"Original Message: {display_text}")
        
        if source == "AUDIO_FILE":
             print(f"WER (STT Accuracy): {calculated_wer:.4f}")
             
        print("\nSIMULATED HAPTIC OUTPUT (Data Stream for Deaf-Blind User)")
        print(f">>>> {braille_output} <<<<")
        print("\n--- ANALYTICS ---")
        print(f"Contraction Ratio (Efficiency): {ratio:.3f}")
        print(f"Translation Core Time: {translation_time:.3f}s")
        print("="*50)

if __name__ == "__main__":
    run_unified_demo()