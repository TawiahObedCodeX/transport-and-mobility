// App.jsx — The main MOVA chat interface component
//
// This is the ENTIRE chat application. It looks like a ChatGPT-style
// messaging interface with a dark navy theme, animated elements, and
// a polished user experience.
//
// HOW IT WORKS:
//   1. When the page loads, we create a unique session ID so the
//      Flask backend can remember this conversation across requests
//   2. A welcome message from MOVA appears immediately (no API call)
//   3. When you type a message and press Enter or click Send:
//      a. Your message appears in a blue bubble on the right
//      b. We POST it to the Flask server at http://localhost:5000/chat
//      c. Bouncing dots show "MOVA is thinking..." while waiting
//      d. MOVA's reply appears in a dark bubble on the left
//   4. The chat auto-scrolls to the newest message
//   5. The textarea auto-resizes as you type

import { useState, useEffect, useRef, useCallback } from 'react'  // React hooks for managing state, effects, refs, and memoized callbacks
import axios from 'axios'                                         // Axios sends HTTP requests to our Flask backend server
import { v4 as uuidv4 } from 'uuid'                               // Generates a random unique ID for this chat session
import './App.css'                                                // Minimal global CSS (just hides body overflow)

// The URL of our Flask backend server that talks to Gemini AI
const API_URL = 'http://localhost:5000'


// ============================================================
// HELPER — Format message text for display
//
// Converts plain text with markdown-style formatting into HTML:
//   - **bold text** becomes <strong>bold text</strong>
//   - Bullet points (•) get indentation
//   - Newlines (\n) become <br/> line breaks
//
// Returns an object with __html so we can use dangerouslySetInnerHTML
// ============================================================

function formatMessageText(text) {
  // Start with the raw text
  let html = text

  // Convert **bold** markers to <strong> HTML tags
  // The regex finds text between double asterisks and wraps it
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

  // Convert bullet points (lines starting with •) into indented list items
  // We add a left margin and a bullet marker style
  html = html.replace(/^•\s(.+)$/gm, '<span class="block ml-2">• $1</span>')

  // Convert newline characters to HTML <br/> line breaks
  html = html.replace(/\n/g, '<br/>')

  // Return in the format React needs for dangerouslySetInnerHTML
  return { __html: html }
}


// ============================================================
// HELPER — Format timestamp for display
//
// If the message was sent less than 60 seconds ago, show "Just now".
// Otherwise show the time in 12-hour format like "2:34 PM".
// ============================================================

function formatTimestamp(date) {
  // Calculate how many seconds have passed since this message
  const secondsAgo = Math.floor((new Date() - new Date(date)) / 1000)

  // If less than 60 seconds, it's still "Just now"
  if (secondsAgo < 60) {
    return 'Just now'
  }

  // Otherwise, format the time in 12-hour clock format (e.g. "2:34 PM")
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',      // Show hour without leading zero (2, not 02)
    minute: '2-digit',    // Always show two digits for minutes
    hour12: true           // Use 12-hour clock with AM/PM
  })
}


// ============================================================
// MAIN APP COMPONENT
// ============================================================

function App() {

  // ----------------------------------------------------------
  // A) STATE VARIABLES
  //
  // State is data that, when changed, causes React to re-draw
  // the screen. Think of it as the app's "memory."
  // ----------------------------------------------------------

  // messages: the full chat history shown on screen
  // Each message is an object: { id, role: 'user'|'mova', text, timestamp }
  // We start with MOVA's welcome message already loaded (no API call needed)
  const [messages, setMessages] = useState([
    {
      id: 'welcome',                                               // Special fixed ID for the welcome message
      role: 'mova',                                                // Sent by MOVA (appears on the left)
      text: "Welcome aboard! 👋 I'm **MOVA**, your intelligent Transport & Mobility assistant.\n\nI can help you with:\n• 🚌 Bus routes and schedules\n• 🚆 Train and rail information\n• 🚗 Traffic and road updates\n• 🚲 Cycling and walking routes\n• 🅿️ Parking information\n• 🗺️ Journey planning\n\nWhat transport question can I help you with today?",
      timestamp: new Date()                                         // When the message was created
    }
  ])

  // inputValue: whatever the user is currently typing in the text box
  const [inputValue, setInputValue] = useState('')

  // isLoading: true while we wait for the Flask server to reply
  const [isLoading, setIsLoading] = useState(false)


  // ----------------------------------------------------------
  // B) REFS (Bookmarks to DOM elements)
  //
  // Refs are like sticky notes that point to HTML elements.
  // Unlike state, changing a ref does NOT re-draw the screen.
  // ----------------------------------------------------------

  // sessionId: a unique ID for this conversation, generated ONCE when the
  // app loads and never changes. The Flask server uses this to remember
  // what was said before. We use useRef so it persists across re-renders
  // without causing extra re-renders itself.
  const sessionId = useRef(uuidv4())

  // messagesEndRef: points to a hidden div at the bottom of the message
  // list. We scroll this into view whenever a new message arrives.
  const messagesEndRef = useRef(null)

  // textareaRef: points to the <textarea> element so we can:
  //   - Auto-focus it after sending a message
  //   - Auto-resize its height as the user types
  const textareaRef = useRef(null)


  // ----------------------------------------------------------
  // C) AUTO-SCROLL TO LATEST MESSAGE
  //
  // Every time the messages array changes (a new message is added),
  // this effect runs and scrolls the chat to the bottom so the user
  // can always see the newest message without manually scrolling.
  // ----------------------------------------------------------

  useEffect(() => {
    // messagesEndRef.current is the invisible div at the bottom of the chat
    // scrollIntoView() tells the browser: "scroll until this element is visible"
    // behavior: 'smooth' creates a smooth animated scroll instead of a sudden jump
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])  // This effect depends on 'messages' — runs when messages change


  // ----------------------------------------------------------
  // D) AUTO-RESIZE THE TEXTAREA
  //
  // As the user types more text, the textarea grows taller so they
  // can see what they're writing. It starts at one line and grows
  // up to 160px max before showing a scrollbar.
  // ----------------------------------------------------------

  function autoResizeTextarea() {
    // Get the actual textarea DOM element from the ref
    const textarea = textareaRef.current
    if (!textarea) return  // If the element doesn't exist yet, do nothing

    // Reset height to 'auto' so scrollHeight gives us the correct minimum
    textarea.style.height = 'auto'

    // Set the height to match the content (scrollHeight)
    // scrollHeight is the total height needed to show all the text
    // Math.min caps it at 160 pixels so it doesn't grow forever
    textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px'
  }


  // ----------------------------------------------------------
  // E) SEND MESSAGE FUNCTION
  //
  // This is the core function. It:
  //   1. Takes the user's typed message
  //   2. Adds it to the chat as a blue bubble
  //   3. Sends it to the Flask server
  //   4. Adds MOVA's reply to the chat
  //   5. Handles any errors gracefully
  //
  // useCallback memoizes this function so it doesn't get recreated
  // on every render (better performance).
  // ----------------------------------------------------------

  const sendMessage = useCallback(async () => {
    // Get the user's typed text and remove leading/trailing spaces
    const text = inputValue.trim()

    // If the message is empty (just spaces or nothing), ignore it
    if (!text) return

    // Build the user's message object with all the info we need
    const userMsg = {
      id: Date.now(),           // Current timestamp in milliseconds — unique enough for a message ID
      role: 'user',             // This message is from the user (appears on the right)
      text: text,               // The actual message content
      timestamp: new Date()     // When the message was sent
    }

    // Add the user's message to the chat history
    // We use the function form of setMessages (prev => ...) to safely
    // add to whatever the current list is, even if it changed in between
    setMessages(prev => [...prev, userMsg])

    // Clear the input field so the user can type their next message
    setInputValue('')

    // Reset the textarea height back to its minimum size
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }

    // Tell the UI to show the loading indicator (bouncing dots)
    setIsLoading(true)

    // Try to send the message to the Flask backend
    try {
      // POST to the Flask server with the message and session ID
      // axios.post sends JSON automatically and sets the right headers
      const response = await axios.post(`${API_URL}/chat`, {
        message: text,                     // The text the user typed
        session_id: sessionId.current      // Our unique conversation ID (stays the same all session)
      })

      // The server returns: { response: "MOVA's reply...", session_id: "..." }
      const movaReply = response.data.response

      // Build MOVA's response message object
      const movaMsg = {
        id: Date.now() + 1,       // Different ID from the user's message
        role: 'mova',             // This message is from MOVA (appears on the left)
        text: movaReply,          // The reply from the AI
        timestamp: new Date()     // When the reply was received
      }

      // Add MOVA's response to the chat history
      setMessages(prev => [...prev, movaMsg])

    } catch (err) {
      // Something went wrong — server down, network error, rate limit, etc.

      // Try to get a specific error message from the server's JSON response
      // If that's not available, use the JavaScript error message
      // If even that is missing, show a generic message
      const errorMsg = err.response?.data?.error || err.message || 'Something went wrong'

      // Build an error message object (shown as if MOVA is speaking)
      const errorMsgObj = {
        id: Date.now() + 2,
        role: 'mova',
        text: `I encountered an issue: ${errorMsg}\n\nPlease try again in a moment.`,
        timestamp: new Date()
      }

      // Add the error message to the chat
      setMessages(prev => [...prev, errorMsgObj])

    } finally {
      // This runs whether the request succeeded OR failed
      // Turn off the loading indicator
      setIsLoading(false)

      // Put focus back on the textarea so the user can keep typing
      textareaRef.current?.focus()
    }
  }, [inputValue])  // Recreate this function only when inputValue changes


  // ----------------------------------------------------------
  // F) HANDLE KEY DOWN
  //
  // When the user presses Enter (without Shift), send the message.
  // When the user presses Shift+Enter, add a new line instead.
  // ----------------------------------------------------------

  function handleKeyDown(e) {
    // Check if the key pressed is Enter AND Shift is NOT held down
    if (e.key === 'Enter' && !e.shiftKey) {
      // Prevent the default behaviour (which would add a new line)
      e.preventDefault()
      // Send the message
      sendMessage()
    }
    // If Shift+Enter is pressed, we do nothing special —
    // the default browser behaviour adds a new line, which is what we want
  }


  // ----------------------------------------------------------
  // G) RENDER — Build the visual interface
  //
  // This returns JSX (JavaScript XML) which looks like HTML but is
  // actually JavaScript. React converts this into real HTML elements
  // on the page.
  //
  // We use Tailwind CSS utility classes for all styling.
  // The classes are applied via the "className" attribute.
  // ----------------------------------------------------------

  return (
    // ----- OUTER CONTAINER -----
    // Fills the entire browser window (h-screen = 100% height)
    // Dark navy background, flex column stacks children vertically
    <div className="flex flex-col h-screen bg-[#0a0f1e] text-white">

      {/* ===== HEADER ===== */}
      {/* Fixed at the top with a dark glassmorphism effect */}
      <header className="px-6 py-4 bg-[#0d1526] border-b border-blue-900/30 flex items-center justify-between relative overflow-hidden">

        {/* Left side: animated bus icon in a glowing blue circle + title */}
        <div className="flex items-center gap-3">
          {/* Animated bus emoji in a blue glowing circle */}
          <div className="w-10 h-10 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-lg animate-pulse">
            🚌
          </div>
          {/* Title and subtitle stacked vertically */}
          <div>
            {/* Main title: bold, 24px equivalent (text-2xl), white */}
            <h1 className="text-2xl font-bold text-white tracking-tight">
              MOVA
            </h1>
            {/* Subtitle: blue-400 colour, smaller text */}
            <p className="text-sm text-blue-400 -mt-0.5">
              Transport & Mobility AI
            </p>
          </div>
        </div>

        {/* Right side: green pulsing dot with "Online" label */}
        <div className="flex items-center gap-2">
          {/* Green pulsing dot: 8px circle with green background and pulse animation */}
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-lg shadow-green-500/50"></span>
          {/* Online text: small, green-tinted */}
          <span className="text-xs text-green-400/80 font-medium">Online</span>
        </div>

        {/* Animated gradient line at the bottom of the header */}
        {/* Shimmers from blue to purple to blue in a smooth loop */}
        <div className="gradient-line"></div>
      </header>

      {/* ===== MESSAGES AREA ===== */}
      {/* Takes up all remaining vertical space (flex-1), scrollable when content overflows */}
      <div
        className="flex-1 overflow-y-auto px-4 py-6 space-y-6"
        style={{
          // Subtle dot grid pattern background for a modern tech feel
          backgroundImage: 'radial-gradient(circle, #1e3a5f 1px, transparent 1px)',
          backgroundSize: '24px 24px'
        }}
      >

        {/* Loop through every message in the messages array and render it */}
        {messages.map((msg) => (

          // Each message is wrapped in a div with animation on appearance
          <div
            key={msg.id}
            // animate-fade-in makes new messages fade in smoothly
            // animate-slide-up makes them slide up slightly as they appear
            // Both are defined in the Tailwind config in index.html
            className="animate-fade-in animate-slide-up"
          >

            {/* ----- MOVA MESSAGE (left-aligned, dark bubble) ----- */}
            {msg.role === 'mova' && (
              <div className="flex items-start gap-3 max-w-[75%]">
                {/* Avatar: small dark navy circle with bus emoji */}
                <div className="w-9 h-9 rounded-full bg-[#0d1526] border border-blue-900/30 flex items-center justify-center flex-shrink-0 text-base">
                  🚌
                </div>
                {/* Bubble: dark navy with subtle blue border, rounded with flat top-left corner */}
                <div className="bg-[#111d35] border border-blue-900/20 rounded-2xl rounded-tl-sm px-4 py-3">
                  {/* Message text with formatting (bold, bullet points, line breaks) */}
                  <div
                    className="text-sm leading-relaxed text-white"
                    // dangerouslySetInnerHTML lets us render HTML from our formatMessageText function
                    // This is safe because WE control the text format, not the user
                    dangerouslySetInnerHTML={formatMessageText(msg.text)}
                  />
                  {/* Timestamp: small, semi-transparent blue text */}
                  <p className="text-xs text-blue-400/60 mt-1">
                    {formatTimestamp(msg.timestamp)}
                  </p>
                </div>
              </div>
            )}

            {/* ----- USER MESSAGE (right-aligned, blue gradient bubble) ----- */}
            {msg.role === 'user' && (
              <div className="flex justify-end">
                <div className="max-w-[75%]">
                  {/* Bubble: blue gradient background, rounded with flat top-right corner */}
                  <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-2xl rounded-tr-sm px-4 py-3">
                    {/* Message text with formatting (supports bold, bullet points, etc.) */}
                    <div
                      className="text-sm leading-relaxed text-white"
                      dangerouslySetInnerHTML={formatMessageText(msg.text)}
                    />
                  </div>
                  {/* Timestamp: small, semi-transparent blue text, aligned right */}
                  <p className="text-xs text-blue-200/60 mt-1 text-right">
                    {formatTimestamp(msg.timestamp)}
                  </p>
                </div>
              </div>
            )}

          </div>
        ))}

        {/* ----- LOADING INDICATOR (MOVA is thinking...) ----- */}
        {/* Shown only when isLoading is true — three animated bouncing dots */}
        {isLoading && (
          <div className="flex items-start gap-3 max-w-[75%] animate-fade-in">
            {/* MOVA's avatar, same style as regular messages */}
            <div className="w-9 h-9 rounded-full bg-[#0d1526] border border-blue-900/30 flex items-center justify-center flex-shrink-0 text-base">
              🚌
            </div>
            {/* Bubble with three bouncing dots */}
            <div className="bg-[#111d35] border border-blue-900/20 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1">
              {/* Each dot is a small blue circle with a staggered bounce animation */}
              {/* dot-1, dot-2, dot-3 have different animation delays (defined in index.html style) */}
              <span className="dot-1 inline-block w-2 h-2 bg-blue-400 rounded-full mx-0.5"></span>
              <span className="dot-2 inline-block w-2 h-2 bg-blue-400 rounded-full mx-0.5"></span>
              <span className="dot-3 inline-block w-2 h-2 bg-blue-400 rounded-full mx-0.5"></span>
            </div>
          </div>
        )}

        {/* Invisible div at the very bottom — we scroll to this when a new message arrives */}
        <div ref={messagesEndRef} />

      </div>

      {/* ===== INPUT AREA ===== */}
      {/* Fixed at the bottom with a dark background and top border */}
      <div className="bg-[#0d1526] border-t border-blue-900/30 px-4 py-4">

        {/* Inner container: darker background, rounded, with the text field and send button */}
        <div className="flex items-end gap-3 bg-[#111d35] rounded-2xl px-4 py-3 border border-blue-900/20 transition-colors duration-200 max-w-4xl mx-auto">

          {/* Textarea: the typing area that auto-grows as the user types */}
          <textarea
            ref={textareaRef}                                    // Ref for auto-focus and height resize
            className="flex-1 bg-transparent text-white placeholder-blue-400/40 resize-none outline-none text-sm leading-relaxed"
            placeholder="Ask MOVA about transport, routes, schedules..."
            value={inputValue}                                    // Controlled component — value comes from state
            onChange={(e) => {                                    // When the user types:
              setInputValue(e.target.value)                       // Update the input state
              autoResizeTextarea()                                // Grow the textarea height
            }}
            onKeyDown={handleKeyDown}                             // Enter to send, Shift+Enter for new line
            rows={1}                                              // Start as one line tall
            disabled={isLoading}                                  // Can't type while waiting for a reply
            style={{ minHeight: '24px', maxHeight: '160px' }}     // Min and max height limits
          />

          {/* Send button: changes appearance based on whether there's text */}
          <button
            onClick={sendMessage}                                 // Send message when clicked
            disabled={isLoading || !inputValue.trim()}             // Disable while loading or input is empty
            className={`
              rounded-xl p-2.5 transition-all duration-200 flex-shrink-0
              ${inputValue.trim() && !isLoading
                ? 'bg-blue-600 hover:bg-blue-500 active:scale-95 cursor-pointer'  // Active state: bright blue, clickable
                : 'bg-blue-900/30 cursor-not-allowed'                            // Disabled state: dimmed, not clickable
              }
            `}
          >
            {/* SVG paper plane icon (more professional than an emoji) */}
            <svg
              className="w-5 h-5 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              {/* The paper plane path */}
              <path d="M22 2L11 13" />
              <path d="M22 2L15 22L11 13L2 9L22 2Z" />
            </svg>
          </button>

        </div>

        {/* Small centered footer text below the input area */}
        <p className="text-center text-blue-400/30 text-xs py-2">
          MOVA · Transport &amp; Mobility Intelligence
        </p>

      </div>

    </div>
  )
}


// Export the App component so main.jsx can import and render it
export default App
