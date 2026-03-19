# Run these one by one (in Terminal or Cursor terminal)

---

## Step 1: Log in to clasp

**In Terminal, run:**

```bash
cd /Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac/CallCalendarScript_Clasp
clasp login
```

- A **URL** will appear (e.g. `https://accounts.google.com/o/oauth2/...`).
- **Open that URL in your browser** → sign in with the Google account that owns CallCalendarScript → click **Allow**.
- When it says "Authorization successful", you can close the tab. The terminal command will finish.
- If it timed out, run `clasp login` again; it may already be logged in.

---

## Step 2: Script ID (where it is)

- **In this project:** Your Script ID is stored in **`script_id.txt`** in this folder (already filled from your screenshot).
- **In the browser:** When you open your project at [script.google.com](https://script.google.com), the Script ID is in the **address bar** — the long string between `/projects/` and `/edit`:
  ```text
  https://script.google.com/home/projects/14ARxY87Zgj0tBJ0vKqCXFSKpN5v5usuuNqx_7y5mGRYCJz6JL2Z7iAuu/edit
  ```
  The Script ID is: `14ARxY87Zgj0tBJ0vKqCXFSKpN5v5usuuNqx_7y5mGRYCJz6JL2Z7iAuu`

---

## Step 3: Clone the project (pulls all scripts in use)

**Important:** Use only the Script ID — **do not** include `/edit` or the full URL.

Your **Script ID is already in `script_id.txt`**. Just run:

```bash
cd /Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac/CallCalendarScript_Clasp
./2_clone.sh
```

Or with the ID directly (no `/edit`):

```bash
clasp clone 14ARxY87Zgj0tBJ0vKqCXFSKpN5v5usuuNqx_7y5mGRYCJz6JL2Z7iAuu
```

When it finishes, this folder will contain **all** your `.gs` files (the ones in use from your project). Then you can **push** changes with:

```bash
clasp push
```
