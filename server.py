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
#   3. Each browser tab gets its own chat history so multiple
#      users can talk to MOVA at the same time without mixing
#      up their conversations
#
# CRITICAL DESIGN DECISION — Fresh client every request:
#
#   Gemini Chat objects become invalid if the underlying HTTP
#   client is closed (which happens between Flask requests).
#   To fix this, we NEVER store the Chat object itself.
#   Instead we store the conversation as a plain list of
#   {"role": ..., "parts": [{"text": ...}]} dicts.
#
#   On every /chat request we:
#     1. Create a brand new genai.Client()
#     2. Create a brand new chat session using the stored
#        history list so Gemini "remembers" the past
#     3. Send the new message
#     4. Append both sides to our stored history list
#     5. Discard the client and chat object entirely
#
#   This avoids the "client has been closed" error entirely.
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
import time                                        # Lets us pause the program (used for retrying rate-limited requests)
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
# chat session. This is safe because it's just a string of
# text — it doesn't hold any open connections.
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
# Each entry maps a session_id (like "abc-123") to a dict
# that contains the conversation HISTORY as a plain list:
#
#   {
#     "history": [
#       {"role": "user",  "parts": [{"text": "Hello"}]},
#       {"role": "model", "parts": [{"text": "Hi!"}]}
#     ]
#   }
#
# IMPORTANT: We store ONLY text history, NOT Gemini Chat
# objects. This is because Gemini Chat objects hold an open
# HTTP connection to Google's servers, and that connection
# gets closed between Flask requests. By storing just text,
# we can create a brand new Chat on every request and feed
# it the past conversation so it "remembers" everything.
# ============================================================

# A Python dictionary (like a filing cabinet) that stores
# all active chat histories by their unique session ID
# Each value is a dict with a "history" key containing a list
active_sessions: dict = {}


# ============================================================
# SECTION 6 — THE MODEL NAME
#
# We define this once so we don't have to type it repeatedly.
# ============================================================

# The Gemini model to use for all conversations
MODEL_NAME = "gemini-2.0-flash"


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
#
# CRITICAL — How we avoid the "client closed" error:
#   We create a FRESH genai.Client() and FRESH Chat session
#   inside this function EVERY TIME it is called. We feed the
#   Chat the stored conversation history so it remembers the
#   past. Then we throw away the client and chat after the
#   response — they are never stored or reused.
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
    # Look up or create the stored history for this session
    # --------------------------------------------------
    # Get the existing history dict, or create a new empty one
    session_data = active_sessions.get(session_id, {"history": []})

    # Get the plain text list of past messages from the session
    # This is a list of dicts like:
    #   [{"role": "user", "parts": [{"text": "..."}]},
    #    {"role": "model", "parts": [{"text": "..."}]}]
    stored_history = session_data["history"]

    # --------------------------------------------------
    # Create a FRESH Gemini client (new every request)
    # --------------------------------------------------
    # IMPORTANT: We create a brand new genai.Client() here
    # instead of reusing one. This is because the underlying
    # HTTP connection in a client can be closed between Flask
    # requests (especially with Flask's reloader/threading).
    # A fresh client is guaranteed to have an open connection.
    #
    # This is the KEY FIX for the "client has been closed" error.
    try:
        # Create a brand new connection to Google's AI servers
        fresh_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        # If we can't even create the client, something is wrong
        return jsonify({
            "error": f"Failed to create Gemini client: {str(e)}"
        }), 500

    # --------------------------------------------------
    # Create a FRESH chat session with the stored history
    # --------------------------------------------------
    # We pass stored_history to the "history" parameter.
    # This tells Gemini: "Here's everything we've said before.
    # Pretend this conversation has been going on for a while."
    #
    # The chat session we get back is brand new but it
    # "remembers" the past because we fed it the history.
    try:
        # Create a brand new chat session, seeding it with
        # the full conversation history so far
        fresh_chat = fresh_client.chats.create(
            model=MODEL_NAME,
            config={
                # MOVA's instruction manual from prompt.md
                "system_instruction": SYSTEM_PROMPT,
                # How creative MOVA should be (0 = strict, 1 = wild)
                "temperature": 0.7,
                # Maximum length of each reply (in tokens)
                "max_output_tokens": 2048,
            },
            # Feed in all past messages so the new chat remembers
            history=stored_history,
        )
    except Exception as e:
        # If creating the chat fails, return the error
        return jsonify({
            "error": f"Failed to create chat session: {str(e)}"
        }), 500

    # --------------------------------------------------
    # Send the user's message to Gemini and get MOVA's reply
    # --------------------------------------------------
    try:
        # Send the user's message through the fresh chat session
        # The chat already has the full history loaded, so MOVA
        # knows what was said before
        ai_response = fresh_chat.send_message(user_message)

        # Extract the text from Gemini's response object
        response_text = ai_response.text

    # --------------------------------------------------
    # ERROR HANDLING — Rate limits, auth errors, etc.
    # --------------------------------------------------
    except genai_errors.ClientError as api_error:
        # A ClientError means Google rejected our request.
        # Different codes mean different problems.

        if api_error.code == 429:
            # 429 = rate limit — too many requests too fast
            # Instead of giving up immediately, we wait 15 seconds
            # and then automatically try ONE more time.
            # This makes the agent feel more robust — most rate limits
            # are temporary and clear within a few seconds.
            print("Rate limit hit (429). Waiting 15 seconds then retrying once...")
            time.sleep(60)

            try:
                # Retry sending the message on the same chat session
                # The session still has the full history loaded
                ai_response = fresh_chat.send_message(user_message)
                # Extract the text from the retry's response
                response_text = ai_response.text

            except Exception:
                # If the retry ALSO fails (still rate limited, or a
                # different error), give up and tell the user to wait
                return jsonify({
                    "error": "MOVA is experiencing high demand. Please wait 60 seconds and try again.",
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

    # --------------------------------------------------
    # SAVE THE CONVERSATION HISTORY
    #
    # Now that we have MOVA's reply, we need to save BOTH
    # the user's message and MOVA's reply to our stored history.
    # This way, the NEXT request can create a new chat session
    # that includes this exchange.
    #
    # We append two entries:
    #   1. {"role": "user",  "parts": [{"text": user_message}]}
    #   2. {"role": "model", "parts": [{"text": response_text}]}
    #
    # This format matches what Gemini's history parameter expects.
    # --------------------------------------------------

    # Add the user's message to the stored conversation history
    stored_history.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    # Add MOVA's reply to the stored conversation history
    stored_history.append({
        "role": "model",
        "parts": [{"text": response_text}]
    })

    # Save the updated history back into the sessions dictionary
    # so it persists for the NEXT request from this session
    active_sessions[session_id] = {"history": stored_history}

    # --------------------------------------------------
    # Return MOVA's reply to the frontend
    # --------------------------------------------------
    # Send back the response text and the session_id
    # (the frontend should send this same session_id next time
    # so MOVA remembers what was said before)
    return jsonify({
        "response": response_text,
        "session_id": session_id
    }), 200  # HTTP 200 = Success


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
    # threaded=True allows multiple users to chat at the same time
    # port=5000 is the port the React frontend will connect to
    app.run(debug=True, threaded=True, port=5000)
