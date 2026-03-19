# CallCalendarScript — Local development with clasp

**clasp** is installed. Follow these steps once to link this folder to your Apps Script project. After that, you can edit here and push with `clasp push`.

---

## Step 1: Get your Script ID

1. Open your **CallCalendarScript** project in the browser: [script.google.com](https://script.google.com).
2. In the address bar you’ll see a URL like:
   ```text
   https://script.google.com/home/projects/XXXXXXXXXXXXXX/edit
   ```
3. Copy the long string between `/projects/` and `/edit` — that’s your **Script ID** (e.g. `1a2B3c4D5e6F7g8H9i0J...`).

---

## Step 2: Log in to clasp (one-time)

In a terminal, run:

```bash
clasp login
```

A browser window will open. Sign in with the **same Google account** that owns the CallCalendarScript project and allow access. When it says “Authorization successful”, you can close the tab and return to the terminal.

---

## Step 3: Clone the project into this folder

From the **project root** (where this folder lives):

```bash
cd /Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac/CallCalendarScript_Clasp
clasp clone YOUR_SCRIPT_ID
```

Replace `YOUR_SCRIPT_ID` with the ID you copied in Step 1.

Example:

```bash
cd /Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac/CallCalendarScript_Clasp
clasp clone 1a2B3c4D5e6F7g8H9i0J
```

Clasp will:

- Create `.clasp.json` (project link)
- Pull `appsscript.json` (manifest)
- Pull all `.gs` files from the project into this folder

---

## Step 4: Workflow after clone

| Who        | Action |
|-----------|--------|
| **You**   | Run `clasp push` in this folder to upload local changes to Apps Script. |
| **You**   | Run `clasp pull` to download the latest from Apps Script (e.g. after editing in the browser). |
| **Assistant** | Edit the `.gs` files in this folder; you push and test. |

- **Push:** `cd CallCalendarScript_Clasp && clasp push`
- **Pull:** `cd CallCalendarScript_Clasp && clasp pull`
- **Open in browser:** `clasp open`
- **Run a function:** use the Apps Script editor (Run) or create a deployment; clasp doesn’t run functions.

Your **triggers stay in Google**; they are not stored in this folder. Changing code and pushing only updates the script that those triggers run.

---

## Quick reference

```bash
cd /Users/mohammadkaishmanihar/Downloads/chatgpt_gui_mac/CallCalendarScript_Clasp
clasp login          # once
clasp clone <ID>     # once, with your Script ID
clasp push           # after editing locally
clasp pull           # to get latest from Apps Script
clasp open           # open project in browser
```

When you’ve run **Step 2** and **Step 3**, tell me and we can make changes in the cloned files; you push and test.
