from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from services.gemini_service import GeminiService
from services.tts_service import TTSService
from services.resume_service import ResumeService
from services.eye_tracking_service import EyeTrackingService
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)

app = Flask(__name__, static_folder=None)
CORS(app)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
gemini = GeminiService(api_key=GEMINI_API_KEY)
tts = TTSService(output_dir=TEMP_DIR)
resume_parser = ResumeService()
eye_tracker = EyeTrackingService()


@app.route('/api/evaluate-code', methods=['POST'])
def evaluate_code():
    data = request.json
    question = data.get('question', '')
    code = data.get('code', '')
    language = data.get('language', 'python')

    result = gemini.evaluate_code(question, code, language)
    return jsonify(result)

@app.route('/api/generate-interview-questions', methods=['POST'])
def generate_interview_questions():
    data = request.json
    domain = data.get('domain', 'Full Stack Development')
    difficulty = data.get('difficulty', 'Medium')
    company_mode = data.get('company_mode', 'Startup')
    resume_text = data.get('resume_text', '')

    questions = gemini.generate_interview_questions(domain, difficulty, company_mode, resume_text)
    return jsonify(questions)

@app.route('/api/evaluate-interview', methods=['POST'])
def evaluate_interview():
    data = request.json
    questions_answers = data.get('questions_answers', [])
    domain = data.get('domain', 'Full Stack Development')

    result = gemini.evaluate_interview(questions_answers, domain)
    return jsonify(result)

@app.route('/api/parse-resume', methods=['POST'])
def parse_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are accepted"}), 400

    file_bytes = file.read()
    text = resume_parser.parse(file_bytes)
    
    if not text:
        # Fallback to Gemini PDF understanding if PyPDF2 fails
        result = gemini.parse_pdf_and_extract_info(file_bytes)
        if result and result.get("text"):
            return jsonify({"text": result["text"], "info": result.get("info", {})})
        return jsonify({"error": "Could not extract text from the PDF"}), 400

    info = gemini.extract_interview_info(text)
    return jsonify({"text": text, "info": info})

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    data = request.json
    text = data.get('text', '')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    os.makedirs(TEMP_DIR, exist_ok=True)

    filepath = tts.generate(text)
    if not filepath:
        return jsonify({"error": "TTS generation failed"}), 500

    response = send_file(
        filepath,
        mimetype='audio/mp3',
        as_attachment=False,
        download_name='speech.mp3'
    )

    @response.call_on_close
    def cleanup():
        tts.cleanup(filepath)

    return response

@app.route('/api/analyze-eyes', methods=['POST'])
def analyze_eyes():
    data = request.json
    image_b64 = data.get('image', '')

    if not image_b64:
        return jsonify({"looking_at_screen": True, "warning": None})

    result = eye_tracker.analyze(image_b64)
    return jsonify(result)

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    data = request.json
    audio_data = data.get('audio', '')
    mime_type = data.get('mime_type', 'audio/webm')

    if not audio_data:
        return jsonify({"error": "No audio data provided"}), 400

    if ',' in audio_data:
        audio_data = audio_data.split(',', 1)[1]

    text = gemini.transcribe_audio(audio_data, mime_type)
    return jsonify({"text": text})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Interview Simulator API is running"})

@app.route('/')
def serve_index():
    response = send_from_directory(FRONTEND_DIR, 'index.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/<path:path>')
def serve_static(path):
    response = send_from_directory(FRONTEND_DIR, path)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

if __name__ == '__main__':
    os.makedirs(TEMP_DIR, exist_ok=True)
    print("=" * 60)
    print("  Syntatic — Interview Simulator")
    print("  Running on http://localhost:5000")
    print("=" * 60)
    app.run(debug=False, port=5000, host='0.0.0.0')
