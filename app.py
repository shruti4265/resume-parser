from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import re
import docx
import PyPDF2
import tempfile
import logging
import uuid
import pandas as pd


try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
logging.basicConfig(level=logging.INFO)

known_skills = {
    "Python", "Machine Learning", "Deep Learning", "Data Analysis", "SQL",
    "C++", "Communication", "Problem Solving", "HTML", "CSS", "JavaScript"
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
                text += pytesseract.image_to_string(image)
    except Exception as e:
        logging.error(f"Error reading PDF file: {e}")
    return text

def extract_text_from_docx(docx_path):
    try:
        doc = docx.Document(docx_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logging.error(f"Error reading DOCX file: {e}")
        return ""

def extract_text_from_txt(txt_path):
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logging.error(f"Error reading TXT file: {e}")
        return ""

def extract_contact_info(text):
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    email = email_match.group() if email_match else "Email not found"

    phone_match = re.search(r'(\+?\d[\d\s().-]{8,})', text)
    phone = phone_match.group().strip() if phone_match else "Phone not found"

    return email, phone

def extract_name(text):
    lines = text.strip().splitlines()

    for line in lines[:10]:
        line = line.strip()
        if not line:
            continue

        if any(char.isdigit() for char in line) or "@" in line or "www" in line.lower():
            continue

        words = line.split()
        capitalized_words = [word for word in words if word.istitle() and word.isalpha()]

        if 1 < len(capitalized_words) <= 4:
            return " ".join(capitalized_words)

    return "Name not found"

def cleanup_files(files_paths):
    for path in files_paths:
        try:
            os.remove(path)
        except Exception as e:
            logging.warning(f"Could not delete file {path}: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({"error": "No files uploaded"}), 400

    results = []
    skills_summary = ""
    saved_file_paths = []

    for file in files:
        tmp_dir = tempfile.mkdtemp()
        file_path = os.path.join(tmp_dir, file.filename)
        file.save(file_path)
        saved_file_paths.append(file_path)

        ext = os.path.splitext(file.filename)[1].lower()
        text = ""

        if ext == ".pdf":
            text = extract_text_from_pdf(file_path)
        elif ext == ".docx":
            text = extract_text_from_docx(file_path)
        elif ext == ".txt":
            text = extract_text_from_txt(file_path)
        else:
            cleanup_files(saved_file_paths)
            return jsonify({"error": f"Unsupported format: {file.filename}"}), 400

        email, phone = extract_contact_info(text)
        name = extract_name(text)

        words = set(word.lower() for word in re.findall(r'\b\w+\b', text))
        lower_known_skills = set(skill.lower() for skill in known_skills)
        matched_skills = sorted(words.intersection(lower_known_skills))

        results.append({
            "Name": name,
            "Email": email,
            "Phone": phone,
            "Skills": ", ".join(matched_skills) if matched_skills else "None"
        })

        skills_summary += f"Name: {name}\nSkills: {', '.join(matched_skills) if matched_skills else 'None'}\n\n"

    cleanup_files(saved_file_paths)

    result_folder = os.path.join("static", "results")
    os.makedirs(result_folder, exist_ok=True)

    unique_id = str(uuid.uuid4())
    csv_filename = f"resume_results_{unique_id}.csv"
    csv_path = os.path.join(result_folder, csv_filename)
    pd.DataFrame(results).to_csv(csv_path, index=False)

    summary_filename = f"skills_summary_{unique_id}.txt"
    summary_path = os.path.join(result_folder, summary_filename)
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(skills_summary.strip())

    return jsonify({
        "results": results,
        "summary": skills_summary.strip(),
        "csv_url": f"/static/results/{csv_filename}",
        "summary_url": f"/static/results/{summary_filename}"
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
