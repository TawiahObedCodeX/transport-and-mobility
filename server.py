# ============================================================
# server.py — Flask API server for the MOVA AI agent
#
# This file turns MOVA into a web service that a React app
# can talk to. Instead of typing in the terminal, the frontend
# sends HTTP requests and gets JSON responses back.
#
# HOW IT WORKS:
#   1. The React frontend sends a POST request to /chat
#      with { "message": "...", "session_id": "..." }
#   2. This server looks up that session's chat history,
#      sends the message to Gemini, and returns MOVA's reply
#   3. Each browser tab gets its own chat session so multiple
#      users can talk to MOVA at the same time without mixing
#      up their conversations
#
# EVERY LINE BELOW IS COMMENTED so anyone can understand it.
# ============================================================


# ============================================================
# SECTION 1 — IMPORT THE TOOLS WE NEED
#
# flask         = the web framework that handles HTTP requests
# flask-cors    = lets the React frontend (different port) talk to us
# uuid          = creates unique session IDs for each user
# os            = reads the secret API key from .env
# Path          = handles file paths on any computer
# load_dotenv   = reads the .env file
# genai         = Google's library for talking to Gemini AI
# genai_errors  = special error types Gemini might throw
# ============================================================

from flask import Flask, request, jsonify          # Flask web server tools
from flask_cors import CORS                        # Lets React talk to Flask (different ports)
import uuid                                        # Creates random unique IDs for each chat session
import os                                          # Reads the secret API key from .env
from pathlib import Path                           # Helps find files on any computer
from dotenv import load_dotenv                     # Reads the .env file
from google import genai                           # Google's official Gemini AI library
from google.genai import errors as genai_errors    # Special error types from Gemini


# ============================================================
# SECTION 2 — SET UP FLASK
#
# Flask is a mini web server. We create one and turn on CORS
# so a React app running on a different port can call us.
# ============================================================

# Create the Flask web server
app = Flask(__name__)

# Turn on CORS (Cross-Origin Resource Sharing)
# This allows the React frontend (e.g. http://localhost:3000)
# to make requests to this server (port 5000) without being blocked
CORS(app)


# ============================================================
# SECTION 3 — LOAD THE SECRET API KEY
#
# Read GEMINI_API_KEY from the .env file. If it's missing,
# print an error but don't crash — the /health endpoint can
# still report that the server is alive.
# ============================================================

# Tell python-dotenv to read the .env file
load_dotenv()

# Get the Gemini API key from the environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# If the key is missing, print a warning to the server console
# The server can still start so the /health endpoint works
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set in .env")
    print("The /chat endpoint will return errors until you add it.")


# ============================================================
# SECTION 4 — LOAD MOVA'S SYSTEM PROMPT
#
# Read prompt.md — MOVA's personality instruction manual.
# We load it once at startup and reuse it for every new
# chat session.
# ============================================================

# Find prompt.md in the same folder as this file
PROMPT_PATH = Path(__file__).parent / "prompt.md"

# Try to read the prompt file
try:
    # Open the file, read everything, then close automatically
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
    print(f"Loaded MOVA system prompt from {PROMPT_PATH}")
except Exception as e:
    # If prompt.md is missing, we can't start
    print(f"ERROR: Could not read {PROMPT_PATH}: {e}")
    SYSTEM_PROMPT = None


# ============================================================
# SECTION 5 — ACTIVE CHAT SESSIONS
#
# This dictionary stores all active conversations.
# Each entry maps a session_id (like "abc-123") to a Gemini
# Chat object that holds that conversation's memory.
#
# When a user sends their first message, we create a new
# Chat and store it here. On subsequent requests, we find
# the existing Chat and keep talking.
# ============================================================

# A Python dictionary (like a filing cabinet) that stores
# all active chat sessions by their unique session ID
active_sessions: dict[str, genai.Chat] = {}


# ============================================================
# SECTION 6 — HELPER: Get or Create a Chat Session
#
# This function looks up a session by its ID.
# If the session exists, it returns the existing Chat.
# If not, it creates a brand new Chat with MOVA's system
# prompt and stores it for future requests.
# ============================================================

def get_or_create_session(session_id: str) -> genai.Chat:
    """
    Find an existing chat session or create a new one.

    session_id: A unique ID string sent by the frontend.
    Returns: A Gemini Chat object with built-in memory.
    """

    # Check if we already have a chat for this session ID
    if session_id in active_sessions:
        # Return the existing chat session — memory is preserved
        return active_sessions[session_id]

    # We don't have one yet, so create a new Gemini client
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Create a fresh chat session with MOVA's personality loaded
    new_chat = client.chats.create(
        model="gemini-2.0-flash",
        config={
            # MOVA's instruction manual from prompt.md
            "system_instruction": SYSTEM_PROMPT,
            # How creative MOVA should be (0 = strict, 1 = wild)
            "temperature": 0.7,
            # Maximum length of each reply (in tokens)
            "max_output_tokens": 2048,
        }
    )

    # Store the new session so we can find it next time
    active_sessions[session_id] = new_chat

    # Let the server admin know a new conversation started
    print(f"Created new chat session: {session_id}")

    # Return the freshly created chat
    return new_chat


# ============================================================
# SECTION 7 — ENDPOINT: GET /health
#
# A simple check to see if the server is running.
# The React frontend calls this to make sure MOVA is online.
# ============================================================

@app.route("/health", methods=["GET"])
def health_check():
    """
    Return a JSON status saying the server is alive.
    The React frontend uses this to verify connectivity.
    """

    # Return a JSON response with status ok and the agent name
    return jsonify({
        "status": "ok",
        "agent": "MOVA"
    }), 200  # HTTP 200 = success


# ============================================================
# SECTION 8 — ENDPOINT: POST /chat
#
# The main endpoint. The React frontend sends:
#   { "message": "What is a BRT system?", "session_id": "abc-123" }
#
# And this endpoint returns:
#   { "response": "BRT stands for Bus Rapid Transit..." }
#
# The session_id tells us which conversation this belongs to.
# If no session_id is sent, we create one automatically.
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():
    """
    Accept a user message, send it to MOVA (Gemini),
    and return MOVA's reply as JSON.
    """

    # --------------------------------------------------
    # GUARD 1 — Check the API key is configured
    # --------------------------------------------------
    # If there's no API key, all AI calls will fail
    if not GEMINI_API_KEY:
        # Return an error with HTTP 503 (Service Unavailable)
        return jsonify({
            "error": "Server not configured: GEMINI_API_KEY is missing"
        }), 503

    # --------------------------------------------------
    # GUARD 2 — Check the system prompt loaded properly
    # --------------------------------------------------
    if not SYSTEM_PROMPT:
        # If prompt.md couldn't be read, return an error
        return jsonify({
            "error": "Server not configured: prompt.md is missing"
        }), 503

    # --------------------------------------------------
    # GUARD 3 — Parse the JSON body from the request
    # --------------------------------------------------
    # Get the JSON data the frontend sent
    data = request.get_json(silent=True)

    # If the body is not valid JSON, return an error
    if data is None:
        return jsonify({
            "error": "Invalid JSON body. Send {'message': '...', 'session_id': '...'}"
        }), 400  # HTTP 400 = Bad Request

    # --------------------------------------------------
    # Extract the user's message from the JSON
    # --------------------------------------------------
    user_message = data.get("message", "").strip()

    # If the message is missing or blank, return an error
    if not user_message:
        return jsonify({
            "error": "Missing 'message' field. Please include your message text."
        }), 400  # HTTP 400 = Bad Request

    # --------------------------------------------------
    # Get or create the session ID
    # --------------------------------------------------
    # If the frontend sent a session_id, use it
    # If not, generate a brand new one for them
    session_id = data.get("session_id", str(uuid.uuid4()))

    # --------------------------------------------------
    # Find or create the chat session for this user
    # --------------------------------------------------
    try:
        # Look up the session's chat history, or start a new one
        chat_session = get_or_create_session(session_id)
    except Exception as e:
        # If creating the session fails (e.g. API key issue)
        return jsonify({
            "error": f"Failed to create chat session: {str(e)}"
        }), 500  # HTTP 500 = Internal Server Error

    # --------------------------------------------------
    # Send the message to Gemini and get MOVA's reply
    # --------------------------------------------------
    try:
        # Send the user's message through the chat session
        # The session automatically remembers all previous messages
        ai_response = chat_session.send_message(user_message)

        # Extract the text from Gemini's response object
        response_text = ai_response.text

        # Return MOVA's reply along with the session_id
        # (the frontend should send this same session_id next time)
        return jsonify({
            "response": response_text,
            "session_id": session_id
        }), 200  # HTTP 200 = Success

    # --------------------------------------------------
    # ERROR HANDLING — Rate limits
    # --------------------------------------------------
    except genai_errors.ClientError as api_error:
        # A ClientError means Google rejected our request.
        # Different codes mean different problems.

        if api_error.code == 429:
            # 429 = rate limit — too many requests too fast
            return jsonify({
                "error": "Rate limit reached. Please wait a moment and try again.",
                "code": 429
            }), 429

        elif api_error.code == 403:
            # 403 = auth error — API key is invalid or expired
            return jsonify({
                "error": "Authentication failed. Check your GEMINI_API_KEY.",
                "code": 403
            }), 403

        elif api_error.code == 400:
            # 400 = bad request — message format issue
            return jsonify({
                "error": f"Bad request: {api_error.message}",
                "code": 400
            }), 400

        else:
            # Any other client error
            return jsonify({
                "error": f"API error ({api_error.code}): {api_error.message}",
                "code": api_error.code
            }), 400

    # --------------------------------------------------
    # ERROR HANDLING — Server errors from Google
    # --------------------------------------------------
    except genai_errors.ServerError as server_error:
        # A ServerError means Google's AI servers had a problem
        return jsonify({
            "error": f"Gemini server error: {server_error.message}"
        }), 502  # HTTP 502 = Bad Gateway

    # --------------------------------------------------
    # ERROR HANDLING — Everything else
    # --------------------------------------------------
    except Exception as unexpected_error:
        # Network issues, timeouts, or anything unexpected
        return jsonify({
            "error": f"Unexpected error: {str(unexpected_error)}"
        }), 500  # HTTP 500 = Internal Server Error


# ============================================================
# SECTION 9 — START THE SERVER
#
# This runs when we type: python server.py
# Flask starts listening on http://localhost:5000
# ============================================================

# This check means: "Only run if this file is executed directly"
if __name__ == "__main__":
    # Print a startup banner so the admin can see it's running
    print()
    print("=" * 60)
    print("  MOVA Server starting...")
    print("  API endpoint: http://localhost:5000")
    print("  Health check: http://localhost:5000/health")
    print("  Chat endpoint: POST http://localhost:5000/chat")
    print("=" * 60)
    print()

    # Start the Flask web server
    # debug=True shows detailed errors in the browser
    # port=5000 is the port the React frontend will connect to
    app.run(debug=True, port=5000)
