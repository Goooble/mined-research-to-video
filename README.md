# mined-research-to-video

## Overview
This project is a Flask-based API that processes research papers (PDF, TXT, DOCX) to generate engaging Instagram reel-style videos. The system extracts text, summarizes it humorously, generates voiceovers, fetches relevant GIFs, and compiles everything into a final video.

## Features
- Extracts text from PDF, TXT, and DOCX files
- Generates a humorous script from research papers using Google Gemini API
- Extracts relevant keywords for GIF retrieval
- Fetches GIFs using the GIPHY API
- Generates an AI voiceover using Google Text-to-Speech (gTTS)
- Creates subtitles and overlays them onto the video
- Produces a final video output with synchronized visuals and audio

## Tech Stack
- **Backend**: Flask (Python)
- **APIs**: Google Gemini API, GIPHY API
- **Media Processing**: MoviePy, FFmpeg, gTTS, Pytesseract (OCR)
- **File Handling**: Python-docx, Fitz (PyMuPDF), Pillow

## Installation
### Prerequisites
- Python 3.x
- FFmpeg installed and added to PATH
- `pip install -r requirements.txt`

### Environment Variables
Set the following environment variables before running the app:
```
export HF_TOKEN="your_huggingface_token"
export GEMINI_API_KEY="your_google_gemini_api_key"
export GIPHY_API_KEY="your_giphy_api_key"
```

## Usage
### Run the Flask Server
```
python app.py
```

### Upload a File for Processing
Send a POST request with a file to `/upload`.

### Download the Processed Video
Visit `/stream_video` to download the generated video.

## File Structure
```
project_folder/
│── new/
│   ├── upload/        # Uploaded files
│   ├── audioClips/    # Audio clips for narration
│   ├── audioFinal/    # Final audio file
│   ├── gifs/          # Retrieved GIFs
│   ├── output/        # Generated video output
│── app.py             # Flask API implementation
│── requirements.txt   # Python dependencies
│── templates/
│   ├── index.html     # Web interface
```

## API Endpoints
### `/upload` (POST)
Uploads a research document and triggers video generation.

### `/stream_video` (GET)
Returns the generated video file.

## Credits
- Developed using Flask, MoviePy, and Google Gemini API
- GIFs powered by GIPHY API


