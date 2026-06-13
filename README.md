<div align="center">

# Noted

**Live meeting transcription and AI-powered meeting minutes.**

Capture audio from your browser, transcribe it in real time with Whisper, and generate structured meeting notes with one click.

[Live Demo](https://noted-ut5g.onrender.com) · [Report Bug](https://github.com/harshalbalar/noted/issues) · [Request Feature](https://github.com/harshalbalar/noted/issues)

---

</div>

## What it does

Noted captures audio directly from your browser — either your microphone or the audio from any browser tab (Zoom, Teams, Google Meet, etc.) — and transcribes it in real time. When your meeting ends, hit one button to generate structured minutes with an executive summary, key takeaways, action items, and a reconstructed dialogue.

No installs. No downloads. Just open the link.

## How it works

```
Browser (mic or tab audio via Web Audio API)
    ↓  WebSocket (audio chunks every 5s)
FastAPI server
    ↓  Groq Whisper API → real-time transcription
    ↓  Gemini API → structured meeting minutes
    ↓  WebSocket
Browser (live transcript + exportable notes)
```

**Transcription** is handled by [Groq](https://groq.com)'s hosted Whisper Large V3 — a purpose-built speech recognition model that transcribes what was actually said, with no hallucination.

**Summarization** is handled by [Google Gemini](https://ai.google.dev) with structured JSON output, producing consistently formatted meeting minutes every time.

## Features

- **Real-time transcription** — audio is chunked, sent over WebSocket, and transcribed as you speak
- **Tab audio capture** — transcribe any meeting happening in a browser tab (Zoom Web, Google Meet, Teams Web)
- **Live waveform visualizer** — real-time frequency visualization using Web Audio API
- **AI meeting minutes** — executive summary, key takeaways, action items, and speaker-attributed dialogue
- **One-click export** — download everything as a `.txt` file
- **Dark interface** — designed for extended use during long meetings
- **No data stored** — audio is processed in memory and never saved to disk

## Quick start

### 1. Clone the repo

```bash
git clone https://github.com/harshalbalar/noted.git
cd noted
```

### 2. Set up environment

```bash
pip install -r requirements.txt
cp .env.example .env
```

### 3. Add your API keys

Edit `.env` with your keys (both are free):

```
GROQ_API_KEY=gsk_your_key_here
GEMINI_API_KEY=your_key_here
```

| Provider | Purpose | Get a key |
|----------|---------|-----------|
| Groq | Audio transcription (Whisper) | [console.groq.com/keys](https://console.groq.com/keys) |
| Gemini | Meeting summarization | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |

### 4. Run

```bash
python main.py
```

Open [http://localhost:8000](http://localhost:8000) in Chrome or Edge.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, WebSockets |
| Frontend | Vanilla HTML/CSS/JS, Web Audio API |
| Transcription | Groq Whisper Large V3 Turbo |
| Summarization | Google Gemini 2.5 Flash |

## Browser support

| Browser | Microphone | Tab audio |
|---------|-----------|-----------|
| Chrome | Yes | Yes |
| Edge | Yes | Yes |
| Firefox | Yes | Limited |
| Safari | Yes | No |

Tab audio capture requires the browser's `getDisplayMedia` API with audio support. When prompted to share your screen, check **"Share audio"** for tab capture to work.

## Project structure

```
noted/
├── main.py              # FastAPI server, WebSocket handler, API routes
├── templates/
│   └── index.html       # Frontend (HTML + CSS + JS, single file)
├── static/              # Static assets directory
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
└── .gitignore
```

## Privacy

- Audio is processed in real-time memory — nothing is written to disk
- Audio chunks are sent to Groq's API for transcription and immediately discarded
- Only the final transcript text is sent to Gemini when you click "Generate Meeting Minutes"
- No analytics, no tracking, no cookies

## License

MIT License. See [LICENSE](LICENSE) for details.
