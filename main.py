import json
import random
import tkinter as tk
import threading
import tempfile
import os
from tkinter import ttk, messagebox
from gtts import gTTS
from playsound import playsound

class FlashcardManager:
    def __init__(self, filename='flashcards.json'):
        self.filename = filename
        self.cards = []
        self.load_cards()

    def load_cards(self):
        try:
            with open(self.filename, 'r') as f:
                self.cards = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.cards = []

    def save_cards(self):
        with open(self.filename, 'w') as f:
            json.dump(self.cards, f, indent=4)

    def add_card(self, question, answer):
        self.cards.append({'question': question, 'answer': answer})
        self.save_cards()

class MainMenu:
    def __init__(self, master, manager):
        self.master = master
        self.manager = manager

        master.title("Flashcard Program")
        master.geometry("300x150")

        ttk.Button(master, text="Add Flashcards", command=self.open_add_window).pack(pady=10)
        ttk.Button(master, text="Practice", command=self.open_practice_window).pack(pady=10)
        ttk.Button(master, text="Quit", command=master.quit).pack(pady=10)

    def open_add_window(self):
        AddFlashcardWindow(self.master, self.manager)

    def open_practice_window(self):
        if not self.manager.cards:
            messagebox.showwarning("No Cards", "Please add flashcards first.")
            return
        PracticeWindow(self.master, self.manager)

class AddFlashcardWindow:
    def __init__(self, master, manager):
        self.manager = manager
        self.window = tk.Toplevel(master)
        self.window.title("Add Flashcard")

        tk.Label(self.window, text="Question:").grid(row=0, column=0, padx=5, pady=5)
        self.question_entry = tk.Text(self.window, width=40, height=4, wrap=tk.WORD)
        self.question_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.window, text="Answer:").grid(row=1, column=0, padx=5, pady=5)
        self.answer_entry = tk.Text(self.window, width=40, height=4, wrap=tk.WORD)
        self.answer_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(self.window, text="Submit", command=self.submit_card).grid(row=2, columnspan=2, pady=10)

    def submit_card(self):
        question = self.question_entry.get("1.0", tk.END).strip()
        answer = self.answer_entry.get("1.0", tk.END).strip()
        if question and answer:
            self.manager.add_card(question, answer)
            self.question_entry.delete("1.0", tk.END)
            self.answer_entry.delete("1.0", tk.END)
            messagebox.showinfo("Success", "Flashcard added!")
        else:
            messagebox.showwarning("Error", "Both fields are required!")

class PracticeWindow:
    def __init__(self, master, manager):
        self.manager = manager
        self.window = tk.Toplevel(master)
        self.window.title("Practice Mode")
        self.window.geometry("600x400")

        # Create card queue with smart shuffling
        self.remaining_indices = list(range(len(self.manager.cards)))
        random.shuffle(self.remaining_indices)
        self.seen_indices = []

        # Card display
        self.card_frame = ttk.Frame(self.window)
        self.card_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        self.card_text = tk.Text(
            self.card_frame,
            wrap=tk.WORD,
            font=('Arial', 14),
            height=8,
            padx=10,
            pady=10
        )
        self.card_text.pack(expand=True, fill=tk.BOTH)
        self.card_text.config(state=tk.DISABLED)

        # Progress label
        self.progress_label = ttk.Label(self.window)
        self.progress_label.pack(pady=5)

        # Buttons
        self.button_frame = ttk.Frame(self.window)
        self.button_frame.pack(pady=10)

        self.show_answer_btn = ttk.Button(
            self.button_frame,
            text="Show Answer",
            command=self.show_answer
        )
        self.show_answer_btn.pack(side=tk.LEFT, padx=5)

        self.correct_btn = ttk.Button(
            self.button_frame,
            text="Correct",
            command=self.mark_correct,
            state=tk.DISABLED
        )
        self.correct_btn.pack(side=tk.LEFT, padx=5)

        self.incorrect_btn = ttk.Button(
            self.button_frame,
            text="Incorrect",
            command=self.mark_incorrect,
            state=tk.DISABLED
        )
        self.incorrect_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            self.button_frame,
            text="Quit",
            command=self.window.destroy
        ).pack(side=tk.LEFT, padx=5)

        self.update_progress()
        self.show_question()

    def speak(self, text):
        def play_audio():
            try:
                tts = gTTS(text=text, lang='en')
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                    temp_filename = fp.name
                tts.save(temp_filename)
                playsound(temp_filename)
                os.remove(temp_filename)
            except Exception as e:
                print(f"Text-to-speech error: {str(e)}")
        
        threading.Thread(target=play_audio).start()

    def update_progress(self):
        total = len(self.manager.cards)
        remaining = len(self.remaining_indices)
        self.progress_label.config(
            text=f"Progress: {total - remaining}/{total} | Remaining: {remaining}"
        )

    def get_next_card(self):
        if not self.remaining_indices:
            self.remaining_indices = self.seen_indices.copy()
            random.shuffle(self.remaining_indices)
            self.seen_indices = []
        
        current_index = self.remaining_indices.pop(0)
        self.seen_indices.append(current_index)
        return current_index

    def show_question(self):
        self.current_index = self.get_next_card()
        card = self.manager.cards[self.current_index]
        
        self.card_text.config(state=tk.NORMAL)
        self.card_text.delete("1.0", tk.END)
        self.card_text.insert(tk.END, card['question'])
        self.card_text.config(state=tk.DISABLED)
        
        self.show_answer_btn.config(state=tk.NORMAL)
        self.correct_btn.config(state=tk.DISABLED)
        self.incorrect_btn.config(state=tk.DISABLED)
        self.update_progress()
        self.speak(card['question'])

    def show_answer(self):
        card = self.manager.cards[self.current_index]
        
        self.card_text.config(state=tk.NORMAL)
        self.card_text.delete("1.0", tk.END)
        self.card_text.insert(tk.END, card['answer'])
        self.card_text.config(state=tk.DISABLED)
        
        self.show_answer_btn.config(state=tk.DISABLED)
        self.correct_btn.config(state=tk.NORMAL)
        self.incorrect_btn.config(state=tk.NORMAL)
        self.speak(card['answer'])

    def mark_correct(self):
        self.next_card()

    def mark_incorrect(self):
        try:
            self.seen_indices.remove(self.current_index)
        except ValueError:
            pass
        
        if len(self.remaining_indices) > 0:
            pos = random.randint(0, len(self.remaining_indices))
        else:
            pos = 0
        self.remaining_indices.insert(pos, self.current_index)
        self.update_progress()
        self.next_card()

    def next_card(self):
        self.show_question()

def main():
    root = tk.Tk()
    flashcard_manager = FlashcardManager()
    MainMenu(root, flashcard_manager)
    root.mainloop()

if __name__ == "__main__":
    main()