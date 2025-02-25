from flask import Flask, render_template, redirect, url_for, request, send_file, after_this_request
from flask_bootstrap import Bootstrap
import speech_recognition as sr
from gtts import gTTS
import os
import tempfile
from pydub import AudioSegment
from dotenv import load_dotenv



load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", "fallback_secret_key")
Bootstrap(app)

@app.route('/')
def home():
    return render_template('home.html')

# Define the 'help' route
@app.route("/help")
def help():
    return render_template("help.html")

@app.route('/audio_text', methods=['GET', 'POST'])
def audio_text():
    if request.method == 'POST':
        r = sr.Recognizer()

        if 'audio_file' not in request.files:
            return render_template("audio_text.html", error="No file uploaded.")

        file = request.files['audio_file']
        if file.filename == '':
            return render_template("audio_text.html", error="No selected file.")

        # Get file extension
        ext = os.path.splitext(file.filename)[1].lower()

        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            temp_file_path = temp_file.name
            file.save(temp_file_path)

        try:
            # Convert to WAV if necessary
            if ext != ".wav":
                audio = AudioSegment.from_file(temp_file_path, format=ext[1:])
                temp_wav_path = temp_file_path.replace(ext, ".wav")
                audio.export(temp_wav_path, format="wav")
                os.remove(temp_file_path)  # Remove original file
                temp_file_path = temp_wav_path  # Use converted file

            with sr.AudioFile(temp_file_path) as source:
                audio_data = r.record(source)
                text = r.recognize_google(audio_data)
                return render_template("audio_text.html", text=text)

        except sr.UnknownValueError:
            error = "Error: Unable to recognize audio."
        except sr.RequestError:
            error = "Error: Could not request results. Check your internet connection."
        except Exception as e:
            error = f"Error: {e}"
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)  # Clean up temp files

        return render_template("audio_text.html", error=error)

    return render_template("audio_text.html")






# Ensure audio directory exists
AUDIO_FOLDER = "static/audio"
AUDIO_FILE = os.path.join(AUDIO_FOLDER, "output.mp3")  # Fixed file path
os.makedirs(AUDIO_FOLDER, exist_ok=True)

def text_to_audio_temp(text):
    """Generate an audio file in the static/audio directory."""
    tts = gTTS(text)
    tts.save(AUDIO_FILE)
    return AUDIO_FILE

@app.route('/text_audio', methods=['GET', 'POST'])
def text_audio():
    audio_file = None

    if request.method == 'POST':
        input_text = request.form['input_text']
        audio_file = text_to_audio_temp(input_text)  # Generate audio

    return render_template("text_audio.html", audio_file=audio_file)

@app.route('/delete_audio')
def delete_audio():
    """Delete the audio file and redirect to the homepage."""
    try:
        if os.path.exists(AUDIO_FILE):
            os.remove(AUDIO_FILE)
    except Exception as e:
        print(f"Error deleting audio file: {e}")

    return redirect('/')  # Redirect to homepage after deletion



@app.route('/real_time')
def real_time():
    return render_template('real_time.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    r = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio_text = r.listen(source, timeout=5)  # 5-second timeout for better UX
            print("Analyzing Speech...")

            recognized_text = r.recognize_google(audio_text)
            return recognized_text
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand. Please try again."
        except sr.RequestError:
            return "Could not process speech. Check your internet connection."
        except Exception as e:
            return f"Error: {e}"

