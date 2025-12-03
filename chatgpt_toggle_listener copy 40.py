# Solution to Improve Text Display and Scrolling in the Interview Assistant

The main issues we need to address are:
1. Flickering during real-time answer display
2. Maintaining focus on the new content being typed
3. Better scroll management during updates

Here's how we can modify the code to fix these issues:

## Key Changes Needed:

1. **Optimize Text Widget Updates**:
   - Instead of rewriting the entire conversation history each time, we'll only update the new content
   - Use text marks to maintain position

2. **Improve Scrolling Behavior**:
   - Track whether the user has manually scrolled away from the bottom
   - Only auto-scroll if they're at the bottom

3. **Reduce UI Updates**:
   - Implement a more efficient buffering system
   - Throttle UI updates more effectively

## Modified Code:

```python
class ChatGPTAssistant:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.streaming = False
        self.current_response = ""
        self.messages = [{"role": "system", "content": "You are a helpful interview assistant. Provide detailed technical answers and ask follow-up questions when appropriate."}]
        self.lock = threading.Lock()
        self.last_scroll_position = 0
        self.font_size = 12
        self.user_scrolled_up = False  # Track if user manually scrolled up

    # ... (keep existing methods unchanged until stream_gpt_response)

    def stream_gpt_response(self, text_widget, status_label, button):
        with self.lock:
            self.current_response = ""
            self.streaming = True
            self.user_scrolled_up = False  # Reset scroll tracking

            # Insert a placeholder in messages list
            placeholder = {"role": "assistant", "content": ""}
            self.messages.append(placeholder)

            # Create a mark for the start of this response
            text_widget.config(state=tk.NORMAL)
            text_widget.insert(tk.END, "Answer: ")
            text_widget.mark_set("response_start", "end-1c")
            text_widget.mark_gravity("response_start", tk.LEFT)
            text_widget.config(state=tk.DISABLED)

            # Configure tags for better appearance
            text_widget.tag_configure('assistant', foreground='#D1D5DB')
            text_widget.tag_configure('user', foreground='#FFFFFF')

            try:
                stream = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=self.messages[:-1],  # exclude placeholder from context
                    stream=True
                )

                buffer = ""
                last_update = time.time()
                update_threshold = 0.05  # 50ms between updates
                char_threshold = 20      # or 20 characters

                for chunk in stream:
                    if not self.streaming:
                        break

                    delta = chunk.choices[0].delta.content if chunk.choices[0].delta else ""
                    if delta:
                        buffer += delta
                        self.current_response += delta
                        placeholder["content"] = self.current_response

                        # Check if we should update the UI
                        current_time = time.time()
                        if (current_time - last_update > update_threshold or 
                            len(buffer) > char_threshold or 
                            delta.endswith(('\n', '.', '!', '?'))):
                            
                            self.update_response_text(text_widget, buffer)
                            buffer = ""
                            last_update = current_time

                            # Check scroll position
                            self.check_scroll_position(text_widget)

                # Final flush of any remaining buffer
                if buffer:
                    self.update_response_text(text_widget, buffer)

            except Exception as e:
                error_msg = f"❌ GPT Error: {str(e)}"
                placeholder["content"] = error_msg
                self.update_response_text(text_widget, error_msg)

            finally:
                self.streaming = False
                button.config(state=tk.NORMAL)
                status_label.config(text="✅ Ready")

    def update_response_text(self, text_widget, new_text):
        """Update only the current response portion of the text widget"""
        text_widget.config(state=tk.NORMAL)
        
        # Get current scroll position
        scroll_pos = text_widget.yview()
        at_bottom = scroll_pos[1] == 1.0
        
        # Insert new text at the response_start mark
        text_widget.insert("response_start", new_text)
        
        # Highlight any code blocks in the new text
        self.highlight_new_code(text_widget, new_text)
        
        text_widget.config(state=tk.DISABLED)
        
        # Auto-scroll only if we were at the bottom before update
        if at_bottom:
            text_widget.see(tk.END)
        
        text_widget.update_idletasks()

    def check_scroll_position(self, text_widget):
        """Check if user has scrolled up manually"""
        scroll_pos = text_widget.yview()
        self.user_scrolled_up = scroll_pos[1] < 0.99  # Leave a small tolerance

    def highlight_new_code(self, text_widget, new_text):
        """Highlight code blocks only in the newly added text"""
        code_blocks = re.finditer(r'```(.*?)```', new_text, re.DOTALL)
        for match in code_blocks:
            start_pos = text_widget.search(match.group(), "response_start", tk.END)
            if start_pos:
                end_pos = f"{start_pos}+{len(match.group())}c"
                text_widget.tag_add('code', start_pos, end_pos)

class Application(tk.Tk):
    # ... (keep existing methods until setup_ui)

    def setup_ui(self):
        # ... (existing setup code until response_box creation)
        
        self.response_box = tk.Text(
            text_frame, wrap=tk.WORD, font=('Consolas', self.assistant.font_size),
            bg='#343541', fg='white', insertbackground='white',
            selectbackground='#4E4E4E', highlightthickness=0
        )
        self.response_box.pack(side="left", fill="both", expand=True)
        self.response_box.insert(tk.END, "🤖 Start a new conversation or ask your first question...")
        self.response_box.config(state=tk.DISABLED)
        
        # Configure tags
        self.response_box.tag_configure('code', foreground='#4EC9B0')
        self.response_box.tag_configure('assistant', foreground='#D1D5DB')
        self.response_box.tag_configure('user', foreground='#FFFFFF')
        
        # Bind scroll event to track user scrolling
        self.response_box.bind("<MouseWheel>", self.on_text_scroll)
        self.response_box.bind("<Button-4>", self.on_text_scroll)  # Linux scroll up
        self.response_box.bind("<Button-5>", self.on_text_scroll)  # Linux scroll down
        
        # ... (rest of existing setup_ui method)

    def on_text_scroll(self, event):
        """Track when user manually scrolls the text widget"""
        self.assistant.user_scrolled_up = True
```

## Key Improvements:

1. **Reduced Flickering**:
   - Instead of rewriting the entire conversation history, we now only update the current response
   - We use text marks to track where the current response begins
   - Updates are more efficiently batched

2. **Better Scrolling**:
   - We track whether the user has manually scrolled up
   - Auto-scroll only happens if the user is at the bottom of the text
   - Scroll position is preserved when new content arrives

3. **Performance Optimizations**:
   - More efficient highlighting that only processes new text
   - Better throttling of UI updates
   - Reduced unnecessary widget redraws

4. **Visual Improvements**:
   - Added different colors for user vs assistant messages
   - More consistent code highlighting

## Additional Recommendations:

1. For even better performance, consider:
   - Using a custom text widget with double buffering
   - Implementing a more sophisticated diffing algorithm for updates
   - Adding a loading indicator during initial response generation

2. For the scroll behavior:
   - You might want to add a "scroll to bottom" button when new content arrives
   - Consider adding smooth scrolling animations

These changes should significantly improve the user experience while maintaining all the existing functionality of your interview assistant application.