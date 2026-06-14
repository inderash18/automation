# ShortsFlow: AI YouTube Shorts Generator

ShortsFlow is a complete, production-ready YouTube Shorts automation dashboard that runs locally. Enter any topic, click "Generate", and watch a fully-rendered vertical YouTube Short compile right before your eyes, complete with high-retention AI script hook, natural voiceover speech, topic-relevant stock video clips, and kinetic styled captions.

---

## Key Features

- **Local AI Scriptwriter**: Calls local Ollama running the LLaMA 3 model via a subprocess pipeline. Falls back to dynamic script templates if Ollama is not present or running.
- **High-Quality Neural Speech**: Converts script text to speech utilizing free Microsoft neural voices via `edge-tts` (defaults to `en-US-EmmaNeural`).
- **Smart Video Fetching**: Queries the Pexels API using the portrait orientation filter to retrieve high-resolution matching vertical videos.
- **Zero-Dependency Captions**: Renders and overlays kinetic uppercase yellow subtitles with thick outline borders utilizing Pillow. **No ImageMagick installation is required!**
- **Sleek Web Interface**: Modern glassmorphic dark-theme dashboard featuring interactive step-by-step loading state animations and an HTML5 9:16 vertical video player to preview and download.

---

## Folder Structure

```text
ai-video-generator/
│
├── backend/
│   ├── app.py              # Main Flask server & routes
│   ├── script_generator.py # Ollama subprocess and template fallbacks
│   ├── voice.py            # Edge-TTS script-to-speech module with WebVTT subtitles
│   ├── stock.py            # Pexels video search / downloader & gradient generator
│   └── video_builder.py    # MoviePy vertical cropping & Pillow subtitle overlay
│
├── frontend/
│   ├── index.html          # Web dashboard layout
│   ├── style.css           # Premium dark styles & animations
│   └── app.js              # Fetch requests & dashboard interactivity
│
├── output/
│   └── final.mp4           # Final compiled Short video output
│
├── temp/                   # Temporary cache directory for processing
├── requirements.txt        # Backend python packages list
├── .env                    # System configurations (contains API Key)
└── README.md               # Setup and execution instructions (this file)
```

---

## Installation & Setup

### Prerequisites

1. **Python 3.8 to 3.11** installed on your system.
2. **Ollama** installed on your system (optional but recommended for custom scripts).
   - Download Ollama from: [https://ollama.com](https://ollama.com)
   - Open your terminal and pull the LLaMA 3 model:
     ```bash
     ollama pull llama3
     ```
3. **Pexels API Key** (optional, for real stock video clips).
   - Get a free developer key from: [https://www.pexels.com/api/](https://www.pexels.com/api/)
   - If not configured, ShortsFlow automatically generates a dynamic animated gradient background instead.

---

### Step-by-Step Execution

#### 1. Clone or copy files to your workspace
Ensure the project structure matches the layout above.

#### 2. Configure Environment Variables
Open the `.env` file in the root directory and add your Pexels API key:
```env
PEXELS_API_KEY=your_actual_pexels_api_key_here
FLASK_PORT=5000
FLASK_DEBUG=True
```

#### 3. Set Up Virtual Environment & Install Dependencies
Open your terminal inside the root `ai-video-generator` directory and run:

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**On Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Run the Server
With the virtual environment activated, run:
```bash
python backend/app.py
```
You should see output indicating the server is running:
`* Running on http://127.0.0.1:5000`

#### 5. Generate Videos!
1. Open your web browser and navigate to `http://127.0.0.1:5000`.
2. Type in a topic (e.g. `the future of artificial intelligence` or `why sleep is a superpower`).
3. Click **Generate Short Video**.
4. Wait 30-60 seconds for the pipeline animation to complete.
5. Preview your new video directly in the simulated phone mockup.
6. Click **Download MP4** to save the video for YouTube upload!

---

## Error Handling & Fallbacks

ShortsFlow is designed to keep running even if some integrations fail:
- **Ollama Fails or Missing**: The backend intercepts execution errors and immediately generates a high-quality viral script from pre-defined templates containing variables mapped to your topic.
- **Pexels API Fails or Missing API Key**: Generates a beautiful dynamic vertical gradient backdrop in the target resolution using a procedural color-cycling system.
- **Edge-TTS Fails**: The system retries synthesis once. If a VTT subtitle is missing, `video_builder` automatically estimates timings mathematically using word-count durations.
- **Merging/Codec Errors**: Failures are printed clearly in the backend console logs and returned to the UI as warning banner messages.
