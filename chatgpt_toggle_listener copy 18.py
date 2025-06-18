import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox
import threading
import pyaudio
import wave
import openai

# (Optional) Set OpenAI API key or expect it to be set in environment
openai.api_key = "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"

class ChatAssistantApp:
    def __init__(self):
        # Initialize main window
        self.root = tk.Tk()
        self.root.title("Chat Assistant")
        self.root.geometry("600x400")
        
        # State for audio recording
        self.is_recording = False
        self.audio_processing = False
        self.recording_tab_index = None
        
        # Create Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.notebook.bind("<Button-3>", self.on_tab_right_click)
        self.notebook.bind("<Double-Button-1>", self.on_tab_double_click)
        
        # Data for tabs: list of sessions, each with its own widgets and history
        self.tabs_data = []
        self.tab_counter = 1  # to assign default names like Chat 1, Chat 2, ...
        
        # Add the special '+' tab for adding new sessions first
        self._add_plus_tab()

        # Now create the first chat tab before '+'
        self.add_new_tab()

        
        # Input frame (for Entry and buttons)
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill='x', side='bottom', padx=5, pady=5)
        # Text entry for user input
        self.user_entry = tk.Entry(input_frame)
        self.user_entry.pack(side='left', fill='x', expand=True, padx=(0,5))
        self.user_entry.bind("<Return>", lambda event: self.send_message())
        # Send button
        send_button = tk.Button(input_frame, text="Send", command=self.send_message)
        send_button.pack(side='left', padx=(0,5))
        # Mic (record) button
        self.record_button = tk.Button(input_frame, text="Record", command=self.toggle_recording)
        self.record_button.pack(side='left')
    
    def _add_plus_tab(self):
        """Add the permanent '+' tab (new tab trigger) to the notebook."""
        plus_frame = ttk.Frame(self.notebook)
        self.notebook.add(plus_frame, text="+")
    

    def add_new_tab(self):
        """Create a new chat tab with its own text area and history."""
        title = f"Chat {self.tab_counter}"
        self.tab_counter += 1

        new_frame = ttk.Frame(self.notebook)
        text_area = scrolledtext.ScrolledText(new_frame, wrap='word', state='disabled')
        text_area.pack(fill='both', expand=True, padx=5, pady=5)

        session_data = {"frame": new_frame, "text_widget": text_area, "history": []}
        self.tabs_data.append(session_data)

        end_index = self.notebook.index("end")

        # If the '+' tab already exists, insert before it. Otherwise, insert at the end.
        insert_index = end_index
        for i in range(end_index):
            if self.notebook.tab(i, "text") == "+":
                insert_index = i
                break

        self.notebook.insert(insert_index, new_frame, text=title)
        self.notebook.select(insert_index)


    
    def on_tab_changed(self, event):
        """Handle tab selection changes, including clicking the '+' tab to add a new one."""
        current_index = self.notebook.index("current")
        # If the '+' tab is selected, create a new tab session
        if self.notebook.tab(current_index, "text") == "+":
            # The last tab (plus) was selected – create a new chat tab
            self.add_new_tab()
    
    def on_tab_double_click(self, event):
        """Handle double-click on a tab to rename it."""
        # Identify which tab was double-clicked by position
        try:
            index = self.notebook.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return  # not on a tab
        # Ignore if it's the '+' tab
        if self.notebook.tab(index, "text") == "+":
            return
        # Prompt for new name
        new_title = simpledialog.askstring("Rename Tab", "Enter new tab name:", parent=self.root)
        if new_title:
            new_title = new_title.strip()
        if new_title:
            self.notebook.tab(index, text=new_title)
    
    def on_tab_right_click(self, event):
        """Handle right-click on a tab to show a context menu for closing or renaming."""
        try:
            index = self.notebook.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return  # clicked not on a tab area
        # Ignore the '+' tab for context menu
        if self.notebook.tab(index, "text") == "+":
            return
        # Create context menu
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Rename Tab", command=lambda idx=index: self.rename_tab(idx))
        menu.add_command(label="Close Tab", command=lambda idx=index: self.close_tab(idx))
        # Show the popup menu at the cursor location
        menu.tk_popup(event.x_root, event.y_root)
        menu.grab_release()
    
    def rename_tab(self, index):
        """Rename the tab at the given index."""
        # Only rename if not the '+' tab
        if self.notebook.tab(index, "text") == "+":
            return
        new_title = simpledialog.askstring("Rename Tab", "Enter new tab name:", parent=self.root)
        if new_title:
            new_title = new_title.strip()
        if new_title:
            self.notebook.tab(index, text=new_title)
    
    def close_tab(self, index):
        """Close the chat tab at the given index."""
        # Do nothing if '+' tab (should not happen as we guard in the menu)
        if self.notebook.tab(index, "text") == "+":
            return
        # Remove the tab from Notebook and destroy its frame
        self.notebook.forget(index)
        session = self.tabs_data.pop(index)
        session["frame"].destroy()
        # If no tabs left (all chat sessions closed), create a new initial tab
        if len(self.tabs_data) == 0:
            self.tab_counter = 1
            self.add_new_tab()
            # Ensure '+' tab is at end (re-add if it got removed, though we keep it persistent)
            # Remove any existing '+' and add a fresh one to be safe
            for i in range(len(self.notebook.tabs())):
                if self.notebook.tab(i, "text") == "+":
                    # Only one '+' should exist; skip re-adding if found
                    break
            else:
                self._add_plus_tab()
    
    def send_message(self):
        """Send the text from the input entry as a user message in the active tab."""
        text = self.user_entry.get().strip()
        if text == "":
            return  # ignore empty input
        # Determine the active tab session
        active_index = self.notebook.index("current")
        # If somehow '+' is active (should not be, since selecting it creates a tab immediately), ignore
        if self.notebook.tab(active_index, "text") == "+":
            return
        session = self.tabs_data[active_index]
        # Display the user's message in the text area
        session["text_widget"].configure(state=tk.NORMAL)
        session["text_widget"].insert(tk.END, f"You: {text}\n")
        session["text_widget"].configure(state=tk.DISABLED)
        session["text_widget"].see(tk.END)
        # Add user message to this tab's history
        session["history"].append({"role": "user", "content": text})
        # Clear the input entry
        self.user_entry.delete(0, tk.END)
        # Start a thread to generate the assistant's response (to avoid blocking UI)
        threading.Thread(target=self._generate_response, args=(active_index,), daemon=True).start()
    
    def _generate_response(self, tab_index):
        """Query the OpenAI API for a response to the last user message in the given tab (runs in a background thread)."""
        session = None
        try:
            session = self.tabs_data[tab_index]
        except IndexError:
            return  # Tab might have been closed mid-request
        messages = session["history"].copy()  # copy the conversation history for sending
        try:
            # Call OpenAI ChatCompletion API with streaming
            completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, stream=True)
        except Exception as e:
            error_msg = f"[Error] {e}\n"
            # Show the error in the chat window
            self.root.after(0, self._append_text, tab_index, error_msg)
            return
        # Insert assistant label and prepare to stream content
        self.root.after(0, self._append_text, tab_index, "Assistant: ")
        assistant_reply = ""
        try:
            for chunk in completion:
                if chunk.get("choices") and chunk["choices"][0].get("delta"):
                    delta = chunk["choices"][0]["delta"]
                    if "content" in delta:
                        part = delta["content"]
                        assistant_reply += part
                        # Append the streamed part to the text widget
                        self.root.after(0, self._append_text, tab_index, part)
        except Exception as e:
            # Streaming interrupted or error
            error_msg = f"\n[Error] {e}\n"
            self.root.after(0, self._append_text, tab_index, error_msg)
        finally:
            if assistant_reply:
                # Only add to history if we got any content
                session["history"].append({"role": "assistant", "content": assistant_reply})
                # Finish the assistant's message with a newline
                self.root.after(0, self._append_text, tab_index, "\n")
    
    def _append_text(self, tab_index, text):
        """Append text to the text widget of the specified tab (runs on the main thread)."""
        # Ensure the tab still exists
        if tab_index >= len(self.tabs_data):
            return
        text_widget = self.tabs_data[tab_index]["text_widget"]
        text_widget.configure(state=tk.NORMAL)
        text_widget.insert(tk.END, text)
        text_widget.configure(state=tk.DISABLED)
        text_widget.see(tk.END)
    
    def toggle_recording(self):
        """Toggle the microphone recording on/off for voice input."""
        if not self.is_recording:
            # If a previous audio is still processing, prevent starting a new recording
            if self.audio_processing:
                messagebox.showwarning("Please wait", "Audio processing is still in progress. Try again in a moment.")
                return
            # Start recording
            self.is_recording = True
            # Lock the tab index for this recording session
            self.recording_tab_index = self.notebook.index("current")
            if self.notebook.tab(self.recording_tab_index, "text") == "+":
                # If somehow on '+' tab, ignore recording
                self.is_recording = False
                return
            # Update button text to indicate recording
            self.record_button.config(text="Stop")
            # Start a background thread to record audio
            threading.Thread(target=self._record_audio, args=(self.recording_tab_index,), daemon=True).start()
        else:
            # Stop recording
            self.is_recording = False
            self.audio_processing = True  # indicate that processing (transcription) will start
            # Revert button text back to idle state
            self.record_button.config(text="Record")
    
    def _record_audio(self, tab_index):
        """Record audio from the microphone until stop is requested, then transcribe and handle it."""
        # Audio recording parameters
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        audio_interface = pyaudio.PyAudio()
        stream = audio_interface.open(format=FORMAT, channels=CHANNELS,
                                      rate=RATE, input=True,
                                      frames_per_buffer=CHUNK)
        frames = []
        try:
            # Record until is_recording is turned off
            while self.is_recording:
                data = stream.read(CHUNK)
                frames.append(data)
        except Exception as e:
            # Error during recording (e.g., device issue)
            print("Recording error:", e)
        # Stop and close the audio stream
        stream.stop_stream()
        stream.close()
        audio_interface.terminate()
        # Save recorded data to a WAV file
        audio_filename = "recorded_audio.wav"
        wf = wave.open(audio_filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio_interface.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        # Transcribe the audio using OpenAI Whisper
        try:
            with open(audio_filename, "rb") as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)
        except Exception as e:
            transcript = None
            err_msg = f"[Error transcribing audio: {e}]"
            # Display transcription error in the chat
            self.root.after(0, self._append_text, tab_index, err_msg + "\n")
        # If transcription succeeded and there's text, handle it as a user message
        if transcript:
            # Insert the transcribed text into the input and send it as user message
            self.root.after(0, self.handle_transcribed_input, transcript, tab_index)
        # Mark audio processing complete
        self.audio_processing = False
    
    def handle_transcribed_input(self, text, tab_index):
        """Handle the transcribed text as if it was typed by the user in the given tab."""
        # If the tab is still open and valid
        if tab_index < len(self.tabs_data):
            # Select that tab (in case user switched away)
            self.notebook.select(tab_index)
            # Put the transcribed text into the input entry (optional, for user to see)
            self.user_entry.delete(0, tk.END)
            self.user_entry.insert(0, text)
            # Send the message (this will pick up the current tab which we just selected)
            self.send_message()
    
    def run(self):
        self.root.mainloop()

# Create and run the chat assistant application
if __name__ == "__main__":
    app = ChatAssistantApp()
    app.run()
