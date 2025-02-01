from flask import Flask, render_template, jsonify, send_file, redirect
import time
import fitz
import pytesseract
from PIL import Image
from flask import request
import google.generativeai as genai
import os
import requests
import io
import subprocess
import re
from docx import Document
import ffmpeg
from moviepy import VideoFileClip ,concatenate_videoclips, AudioFileClip, CompositeVideoClip, concatenate_audioclips
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.VideoClip import TextClip
from gtts import gTTS, tokenizer
from moviepy import *
import math
import shutil
app = Flask(__name__)

# Load API key from environment variable

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Gets key from environment
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")


GEMINI_API_KEY = "AIzaSyABIkRda73L5Amtj001aP_QFfoLNZHSMNk"
GIPHY_API_KEY = "TVV1SHNjiFkTzcT1U4q4wvJmfp7ZNbpd"
GIPHY_API_URL = "https://api.giphy.com/v1/gifs/search"
genai.configure(api_key=GEMINI_API_KEY)


# Configure Tesseract OCR

UPLOAD_FOLDER = "new/upload"

AUDIOCLIPS_FOLDER = "new/audioClips"
AUDIOFINAL_FOLDER = "new/audioFinal"
GIFS_FOLDER = "new/gifs"
VIDEOOUTPUT_FOLDER = "new/output"
os.makedirs(AUDIOCLIPS_FOLDER, exist_ok=True)
os.makedirs(AUDIOFINAL_FOLDER, exist_ok=True)
os.makedirs(GIFS_FOLDER, exist_ok=True)
os.makedirs(VIDEOOUTPUT_FOLDER, exist_ok=True)

OUTPUT_FOLDER = "outputgem"
GIF_FOLDER = "gifsgem"
VIDEO_FOLDER = "videosgem"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(GIF_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)


# MAX_TOKENS = 10000


def clear_folder(folder_path):
    try:
        shutil.rmtree(folder_path)  # Remove the folder and all its contents
        os.makedirs(folder_path)    # Recreate the folder if needed
    except Exception as e:
        print(f"Error clearing folder: {e}")


# Function to extract text from PDF

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    extracted_text = ""
    for page in doc:
        extracted_text += page.get_text("text") + "\n"
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image = Image.open(io.BytesIO(base_image["image"]))
            extracted_text += pytesseract.image_to_string(image, lang="eng") + "\n"
    print(len(extracted_text.strip()[:100000]))
    return extracted_text.strip()[:100000]
# extract_text_from_pdf("new/upload/research2.pdf")
def extract_text_from_txt(txt_path):
    with open(txt_path, "r", encoding="utf-8") as file:
        return file.read().strip()

# Function to extract text from DOCX file
def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    text = []
    for paragraph in doc.paragraphs:
        text.append(paragraph.text)
    return "\n".join(text).strip()


def generate_script_and_keywords(text):
    prompt = """
    I want you to to generate a 150 word transcript that will used as instagram reel voiceover, 
    i will give you the research paper given above, you should explain and highlight the super intersting points in a humorous way
    the format of your answer should be a colon followed by 5 words each for example-
    
    :This research paper explores
    :<your sentence>
    :<your sentence>
    
    
    and so on,thats how your response should be
    generate 20 such lines
    dont include anything harmful or sexual
    it should be an explainer of the research paper
    """
    model = genai.GenerativeModel("gemini-pro")
    script_prompt = f"{text}\n\n\n:{prompt}"

    
    script_response = model.generate_content(script_prompt)
    keyword_prompt = f"""Extract 15 important terms from the following script, words which are best suited to search for gifs: 
    script:({script_response})
    format it like this:
    
    :enter your gif search term
    :enter your gif search term
    
    and so on, 
    generate 20 such lines
    dont include anything harmful or sexual
    the search term must be below 3 words
    each search term generated must correspond to one sentence of the script sequentially
    do not include "search for" in your response
    keep the search terms generic
    dont be too specific 
    """
    keyword_response = model.generate_content(keyword_prompt)
    
    return script_response.text.strip(), keyword_response.text.strip()


def extractScriptGem(text):
    sentences = [sentence.split(":", 1)[-1].strip() for sentence in text.splitlines() if ":" in sentence]
    text2 = " ".join(sentences)  # Joins with spaces
    return text2

    # Print the extracted sentences
    # for sentence in sentences:
    #     print(sentence)
def extractKeywordsGem(text):
    sentences = [sentence.split(":", 1)[-1].strip() for sentence in text.splitlines() if ":" in sentence]
    return sentences



def save_gif_for_keyword(keyword, gif_prefix, retries=3):
    """
    Request 5 GIFs for the given keyword, then try to download them one by one.
    If one download succeeds, it is saved and the function returns its file path.
    If a download fails, it moves to the next GIF in the list.
    """
    params = {"api_key": GIPHY_API_KEY, "q": keyword, "limit": 5}
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36")
    }
    
    # Fetch GIF data with retries
    for attempt in range(retries):
        try:
            response = requests.get(GIPHY_API_URL, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                gif_data = response.json()
                if not gif_data["data"]:
                    print(f"No GIFs found for the keyword '{keyword}'.")
                    return None
                break  # Successfully retrieved GIF data
            else:
                print(f"Error fetching data for '{keyword}' (Attempt {attempt+1}/{retries}): {response.status_code}")
        except Exception as e:
            print(f"Exception fetching data for '{keyword}' (Attempt {attempt+1}/{retries}): {e}")
        time.sleep(2)
    else:
        print(f"Failed to fetch GIFs for '{keyword}' after {retries} attempts.")
        return None

    # Iterate through the list of GIFs until one successfully downloads
    for idx, gif_info in enumerate(gif_data["data"]):
        gif_url = gif_info["images"]["original"]["url"]
        print(f"Attempting to download GIF {idx+1} for '{keyword}' from: {gif_url}")
        try:
            gif_response = requests.get(gif_url, stream=True, timeout=20)
            if gif_response.status_code == 200:
                gif_filename = f"{gif_prefix}.gif"
                gif_path = os.path.join(GIFS_FOLDER, gif_filename)
                with open(gif_path, "wb") as gif_file:
                    for chunk in gif_response.iter_content(1024):
                        gif_file.write(chunk)
                print(f"Saved GIF for '{keyword}' to: {gif_path}")
                return gif_path  # Return after the first successful download
            else:
                print(f"Error downloading GIF {idx+1} for '{keyword}': HTTP {gif_response.status_code}")
        except Exception as e:
            print(f"Exception downloading GIF {idx+1} for '{keyword}': {e}")

    print(f"Could not download any GIFs for '{keyword}'.")
    return None

def save_gifs_from_keywords(keywords):
    """
    Accepts a newline-separated string of keywords.
    For each keyword, fetch up to 5 GIFs and try to download one.
    The successfully downloaded GIF is saved with a sequential file name.
    Returns a dictionary mapping each keyword to the file path of the downloaded GIF (or None).
    """
    keyword_list = keywords
    results = {}
    gif_counter = 1  # Start numbering from gif1.gif
    
    for keyword in keyword_list:
        print(f"\nProcessing keyword: '{keyword}'")
        saved_path = save_gif_for_keyword(keyword, gif_counter)
        if saved_path is not None:
            results[keyword] = saved_path
            gif_counter += 1  # Increment counter only if a GIF is successfully saved
        else:
            results[keyword] = None
        # Optional: delay between keywords to avoid rate limiting
        time.sleep(1)
        
    return results




def extractScript(text):
    lengthOfWords = 7
    words = text.split()
    sentence = []
    i = 0
    for w in range(0,math.ceil(len(words)/lengthOfWords)):
        sentence.append(" ".join(words[i:i+lengthOfWords]))
        i = i + lengthOfWords
    # print(sentence)
    return sentence

def generateAudio(sentence):

    for i in range(0, len(sentence)):
        text = sentence[i]
        audio = gTTS(text)
        audio.save("new/audioClips/audio{}.mp3".format(i))
    


audioClips = []
textClips = []
audioDuration = 0
def generateSubs(sentence):
    global audioDuration
    for i in range(0, len(sentence)):
        audioClips.append(AudioFileClip("new/audioClips/audio{}.mp3".format(i)))
        audioClips[i] = audioClips[i].with_speed_scaled(1.3).with_section_cut_out(audioClips[i].duration-0.38, audioClips[i].duration)
        audioDuration += audioClips[i].duration
        textClips.append(TextClip(font="fonts/roboto.otf", text = sentence[i],font_size=24, color='black',  text_align='center', bg_color="white", method="caption", size=(450,None), margin=(2,0)))
        textClips[i]=textClips[i].with_duration(audioClips[i].duration)
        if i == 0:
            textClips[i]=textClips[i].with_start(0)
            textClips[i]=textClips[i].with_end(audioClips[i].duration)
        else:
            textClips[i]=textClips[i].with_start(textClips[i-1].end)
    audioDuration = math.floor(audioDuration)
    
def generateVid(length):
    clips = []
    for i in range(1, length):
        clips.append(VideoFileClip("new/gifs/{}.gif".format(i)).subclipped(0,3))
    finalVid = concatenate_videoclips(clips, method="compose").with_background_color(size=(480, 720), color=(255, 255, 255))
    finalVid = finalVid.with_speed_scaled(finalVid.duration/audioDuration)
    finalAud = concatenate_audioclips(audioClips)
    finalText = CompositeVideoClip(textClips).with_position(("center",0.9), relative=True)
    finalText=finalText.with_duration(audioDuration)
    result = CompositeVideoClip([finalVid, finalText], size=(480, 720))
    finalAud.write_audiofile("new/audioFinal/final.mp3")
    result.write_videofile("new/output/promax.mp4", audio="new/audioFinal/final.mp3")


# gemText = extract_text_from_pdf("research.pdf")
# gemScript, gemKeys = generate_script_and_keywords(gemText)  
# sentence = extractScript(extractScriptGem(gemScript))
# print(sentence)
# Keys = extractKeywordsGem(gemKeys)
# print(Keys)

@app.route('/')
def home():
    # # Initialize client
    # client = InferenceClient("black-forest-labs/FLUX.1-dev", token="hf_TdtnOSuYZmmhRUJivDldVRpNBuIvNnKSv")#D

    # # Generate image
    # image = client.text_to_image("physics")

    # image.save("physics.png", format="PNG")

    return render_template("index.html")#files need to be in template folder

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    clear_folder(UPLOAD_FOLDER)
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    clear_folder(AUDIOFINAL_FOLDER)
    clear_folder(AUDIOCLIPS_FOLDER)
    clear_folder(VIDEOOUTPUT_FOLDER)
    clear_folder(GIFS_FOLDER)
    
        
    gemText = extract_text_from_pdf(file_path)
    gemScript, gemKeys = generate_script_and_keywords(gemText)  
    sentence = extractScript(extractScriptGem(gemScript))
    
    Keys = extractKeywordsGem(gemKeys)
    
    generateAudio(sentence)
    generateSubs(sentence)
    # keywords = "kitten\ndog\nduck\nrussia"
    
    download_results = save_gifs_from_keywords(Keys)
    print("\nDownload results:")
    for key, path in download_results.items():
        print(f"{key}: {path}")
    generateVid(len(Keys))
    print(sentence)
    print(Keys)
    time.sleep(10)
    return redirect("/stream_video")

@app.route('/stream_video')
def sendVideo():
    
    return send_file("new/output/promax.mp4", mimetype='video/mp4', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
