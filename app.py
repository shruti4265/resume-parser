import os
import re
import uuid
import logging
import tempfile
import io  # Required for in-memory file handling
import docx
import PyPDF2
import pandas as pd
from flask import Flask, request, jsonify, render_template, session, Response  # Added session and Response
from flask_cors import CORS

# --- Basic App Setup ---
app = Flask(__name__)
# A secret key is required for Flask sessions to work
app.secret_key = os.urandom(24)
CORS(app, resources={r"/*": {"origins": "*"}})
logging.basicConfig(level=logging.INFO)

# --- OCR Setup (Optional) ---
try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# --- Core Logic: Skill Definitions and Extraction Functions ---

# Using a more comprehensive, case-insensitive set for better matching
KNOWN_SKILLS = {
    "python", "machine learning", "deep learning", "data analysis", "sql",
    "c++", "java", "communication", "problem solving", "html", "css", "javascript",
    "react", "vue", "angular", "node.js", "mongodb", "postgresql",
    "docker", "kubernetes", "aws", "azure", "gcp", "pandas", "numpy",
    "scikit-learn", "tensorflow", "pytorch", "flask", "django"
}

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if not text.strip() and OCR_AVAILABLE:
            images = convert_from_path(pdf_path)
            for image in images:
                text += pytesseract.image_to_string(image) + "\n"
    except Exception as e:
        logging.error(f"Error reading PDF file {os.path.basename(pdf_path)}: {e}")
    return text

def extract_text_from_docx(docx_path):
    try:
        doc = docx.Document(docx_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logging.error(f"Error reading DOCX file {os.path.basename(docx_path)}: {e}")
        return ""

def extract_text_from_txt(txt_path):
    try:
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        logging.error(f"Error reading TXT file {os.path.basename(txt_path)}: {e}")
        return ""

def extract_contact_info(text):
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    email = email_match.group(0) if email_match else "Not found"
    phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}', text)
    phone = phone_match.group(0).strip() if phone_match else "Not found"
    return email, phone

def extract_name(text):
    lines = text.strip().splitlines()
    for line in lines[:5]:
        line = line.strip()
        if not line or "@" in line or re.search(r'\d{5,}', line) or \
           line.lower() in ["resume", "curriculum vitae", "cv"]:
            continue
        if 2 <= len(line.split()) <= 4 and re.match(r'^[A-Za-z\s.]+$', line):
            return line
    return "Not found"

def extract_skills(text):
    found_skills = set()
    text_lower = text.lower()
    for skill in KNOWN_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills.add(skill.title())
    return sorted(list(found_skills))

# --- Flask Routes ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "No files selected"}), 400

    all_results = []
    for file in files:
        # Use a temporary directory for robust, automatic cleanup
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, file.filename)
            file.save(file_path)
            ext = os.path.splitext(file.filename)[1].lower()
            text = ""

            if ext == ".pdf": text = extract_text_from_pdf(file_path)
            elif ext == ".docx": text = extract_text_from_docx(file_path)
            elif ext == ".txt": text = extract_text_from_txt(file_path)
            else: continue # Skip unsupported files

            email, phone = extract_contact_info(text)
            name = extract_name(text)
            skills = extract_skills(text)

            all_results.append({
                "Name": name, "Email": email, "Phone": phone,
                "Skills": ", ".join(skills) if skills else "None"
            })

    if not all_results:
        return jsonify({"error": "Could not extract information from the provided files."}), 400

    # Instead of saving files, store the results in the user's session
    session['results_data'] = all_results
    session['skills_summary'] = "\n\n".join(
        f"Name: {res['Name']}\nSkills: {res['Skills']}" for res in all_results
    )

    return jsonify({
        "results": all_results,
        "summary": session['skills_summary']
    }), 200

# New route to handle CSV downloads
@app.route('/download/csv')
def download_csv():
    results_data = session.get('results_data')
    if not results_data:
        return "No data available to download.", 404

    df = pd.DataFrame(results_data)
    # Generate CSV in memory
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=resume_results.csv"}
    )

# New route to handle summary text downloads
@app.route('/download/summary')
def download_summary():
    skills_summary = session.get('skills_summary')
    if not skills_summary:
        return "No data available to download.", 404

    return Response(
        skills_summary,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=skills_summary.txt"}
    )

if __name__ == '__main__':
    app.run(debug=True)
