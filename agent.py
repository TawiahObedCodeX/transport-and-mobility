# ============================================================
# agent.py — MOVA Transport & Mobility AI Agent
#
# This is the main file that runs MOVA.
# MOVA is a chatbot that ONLY answers transport & mobility questions.
# It uses Google's Gemini AI (free tier) as its brain.
#
# HOW IT WORKS:
#   1. Loads MOVA's personality from the file "prompt.md"
#   2. Connects to Google Gemini AI using your secret API key
#   3. Shows MOVA's welcome message
#   4. Enters a loop: user types → MOVA replies → repeat
#   5. When you type "exit" or "quit", MOVA says goodbye and stops
#
# EVERY LINE BELOW IS COMMENTED so anyone can understand it.
# ============================================================


# ============================================================
# SECTION 1 — IMPORT THE TOOLS WE NEED
#
# These are like hiring specialists:
#   - "os" reads environment variables (stored in .env)
#   - "sys" lets us close the program cleanly
#   - "Path" handles file locations on any computer
#   - "load_dotenv" reads our .env file
#   - "genai" is Google's library for talking to Gemini AI
#   - "genai_errors" has special error types Gemini might send us
# ============================================================

import os                               # Lets us read the secret API key from our .env file
import sys                              # Lets us close the program gracefully when needed
from pathlib import Path                # Helps find files no matter what computer we're on
from dotenv import load_dotenv          # Reads the .env file so we can use the API key
from google import genai                # Google's official Python library for Gemini AI
from google.genai import errors as genai_errors  # Special error types that Gemini might throw

# Tell the Windows terminal to use UTF-8 so it can show emojis and symbols
# Some computers use older text settings that break on special characters
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


# ============================================================
# SECTION 2 — LOAD THE SECRET API KEY FROM .env
#
# The .env file is like a locked drawer that stores passwords.
# We NEVER write passwords directly in our code.
# Instead, we read them from .env at startup.
# ============================================================

# Tell python-dotenv to find and read the .env file
load_dotenv()

# Ask Python: "What is the GEMINI_API_KEY value from .env?"
api_key = os.getenv("GEMINI_API_KEY")

# If the key is empty or missing, stop here and explain what to do
if not api_key:
    # Print a clear error message with instructions
    print("=" * 60)
    print("  ERROR: Missing Gemini API Key")
    print("=" * 60)
    print()
    print("  To fix this:")
    print("    1. Open the file named .env in this folder")
    print("    2. Add this line (replace with your real key):")
    print("       GEMINI_API_KEY=your-actual-api-key-here")
    print("    3. Save the file and run agent.py again")
    print()
    print("  Get a free API key at: https://aistudio.google.com")
    print()
    # Exit the program — we can't continue without the key
    sys.exit(1)


# ============================================================
# SECTION 3 — LOAD MOVA'S PERSONALITY FROM prompt.md
#
# The file prompt.md is MOVA's "instruction manual."
# It tells the AI:
#   - Its name is MOVA
#   - It ONLY talks about transport and mobility
#   - How to be warm and friendly
#   - What topics to refuse (like cooking or medicine)
#   - What welcome message to say
#
# We read the whole file as one big string of text.
# ============================================================

# Find prompt.md in the same folder as agent.py
prompt_file_path = Path(__file__).parent / "prompt.md"

# Open the file, read everything into a variable, then close it
# "with" means Python will close the file automatically when done
with open(prompt_file_path, "r", encoding="utf-8") as prompt_file:
    # Read the entire contents of prompt.md into memory
    system_prompt = prompt_file.read()


# ============================================================
# SECTION 4 — CONNECT TO GEMINI AI
#
# We create TWO things:
#   1. A "client" — this is our connection to Google's AI servers
#   2. A "chat session" — this is like opening a new chat window
#
# The chat session is special because it REMEMBERS everything
# we say. That's how MOVA keeps track of the conversation.
# ============================================================

# Create a connection to Google Gemini using our secret key
# "client" is how we talk to Google's AI servers
gemini_client = genai.Client(api_key=api_key)

# Tell Gemini which model to use
# "gemini-2.0-flash" is fast, smart, and free to use
model_to_use = "gemini-2.0-flash"

# Open a new chat session — this is like starting a fresh conversation
# The session has built-in memory, so it remembers everything we say
# "config" tells Gemini HOW to behave
chat_session = gemini_client.chats.create(
    model=model_to_use,  # Which AI brain to use
    config={
        # MOVA's instruction manual — read from prompt.md earlier
        "system_instruction": system_prompt,
        # How creative MOVA should be: 0 = very strict / 1 = very creative
        "temperature": 0.7,
        # Maximum length of each reply (in word-pieces called "tokens")
        "max_output_tokens": 2048,
    }
)


# ============================================================
# SECTION 5 — SHOW MOVA'S WELCOME MESSAGE
#
# Before the user types anything, MOVA greets them warmly.
# We send a "starter" message to trigger MOVA's welcome.
# The welcome text is defined in prompt.md section 6.1.
#
# If the internet is down, we show a simple backup message instead.
# ============================================================

# Print a nice header showing the program is starting
print()
print("=" * 60)
print("  MOVA — Transport & Mobility AI Agent")
print("  Starting up...")
print("=" * 60)
print()

# Try to get MOVA's welcome message from the AI
try:
    # Send a starter message to make MOVA introduce itself
    # The system prompt tells MOVA to always greet new users warmly
    ai_reply = chat_session.send_message(
        "Please start the conversation with your welcome message."
    )

    # Extract the text part from Gemini's reply object
    mova_welcome = ai_reply.text

    # Remove any extra quote marks the AI might have added
    mova_welcome = mova_welcome.strip('"').strip("'")

    # Display MOVA's welcome message to the user
    print(f"MOVA: {mova_welcome}")
    print()

# If something went wrong (like no internet), use a backup message
except Exception:
    # A simple welcome message that doesn't need the internet
    print("(Welcome could not be generated from AI.)")
    print()
    print("MOVA: Welcome aboard! I'm MOVA, your Transport & Mobility")
    print("       Intelligence Agent. I'm here to help with all your")
    print("       transport questions.")
    print()

# Show a small instruction line about how to use the chat
print("Enter your message below. Type 'exit' or 'quit' to end the chat.")
print()


# ============================================================
# SECTION 6 — THE MAIN CHAT LOOP
#
# This is the heart of the program.
# It runs FOREVER (while True) until the user says "exit".
# Each round:
#   1. Wait for the user to type something
#   2. Send it to Gemini AI through the chat session
#   3. Show MOVA's reply
#   4. Go back to step 1
#
# The chat session remembers everything automatically.
# ============================================================

# "while True" means "keep going forever until we tell it to stop"
while True:

    # Ask the user to type a message (input() waits for Enter key)
    # .strip() removes any extra spaces at the start or end
    user_message = input("You: ").strip()

    # If the user pressed Enter without typing, skip and ask again
    if not user_message:
        # Go back to the top of the while loop
        continue

    # Check if the user wants to end the conversation
    # .lower() converts to lowercase so "Exit" / "EXIT" / "exit" all work
    if user_message.lower() in ("exit", "quit"):

        # Try to get a nice goodbye message from the AI
        try:
            # Ask Gemini to say goodbye to the user
            goodbye_reply = chat_session.send_message(
                "Say a brief, warm goodbye to the user."
            )
            # Print MOVA's goodbye message
            print(f"\nMOVA: {goodbye_reply.text}\n")

        # If the AI is unreachable, use a simple backup goodbye
        except Exception:
            print("\nMOVA: Goodbye! Thanks for chatting. Safe travels!\n")

        # Exit the while loop and end the program
        break

    # If we get here, the user typed a real message.
    # Try to talk to Gemini AI and handle any problems that might come up.
    try:
        # Send the user's message through the chat session
        # The session already has all previous history stored in it
        ai_response = chat_session.send_message(user_message)

        # Print MOVA's reply to the screen
        print(f"\nMOVA: {ai_response.text}\n")

    # Handle errors from the Google Gemini API
    except genai_errors.ClientError as api_error:
        # A "ClientError" means Google said our request was bad.
        # Different error codes mean different problems:
        #   429 = rate limit (too many requests too fast)
        #   403 = auth error (API key is invalid)
        #   400 = bad request (message format issue)

        # Check if Google says we sent too many requests
        if api_error.code == 429:
            print()
            print("[Slow down! Too many requests. Please wait 30 seconds and try again.]")
            print()

        # Check if our API key is wrong or expired
        elif api_error.code == 403:
            print()
            print("[Authentication error! Your API key might be wrong or expired.]")
            print("[Check the GEMINI_API_KEY in your .env file.]")
            print()

        # For any other client error, show the error code and message
        else:
            print()
            print(f"[Error {api_error.code}: {api_error.message}]")
            print()

    # Handle errors from Google's servers
    except genai_errors.ServerError as server_error:
        # A "ServerError" means something went wrong on Google's end
        print()
        print(f"[Gemini server had a problem: {server_error.message}]")
        print("[Please wait a moment and try again.]")
        print()

    # Handle any other kind of error (network down, timeout, etc.)
    except Exception as unexpected_error:
        # This catches everything else — internet problems, timeouts, etc.
        print()
        print(f"[Something went wrong: {unexpected_error}]")
        print("[Check your internet connection and try again.]")
        print()


# ============================================================
# SECTION 7 — THE END
#
# When the user says "exit" or "quit", the while loop stops
# and we reach this point. Python ends the program here.
# ============================================================
