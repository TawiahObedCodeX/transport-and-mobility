// main.jsx — The starting point of the MOVA chat application
//
// This file is the first thing that runs when the app loads.
// It finds the empty <div id="root"> in index.html and puts our
// React App component inside it. Think of it as the "front door"
// of the whole application.

import React from 'react'          // The React library — needed for JSX to work
import ReactDOM from 'react-dom/client'  // ReactDOM puts our app into the web page
import App from './App.jsx'        // Our main chat component (the whole app)
import './index.css'               // Global styles that apply to everything

// Find the empty <div id="root"> in index.html and create a "root" there
// ReactDOM.createRoot is the modern way to start a React app
ReactDOM.createRoot(document.getElementById('root')).render(
  // StrictMode helps catch bugs by running effects twice in development
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
