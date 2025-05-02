import os
import pdfplumber
import spacy
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'resumes'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Load the English NLP model from spaCy
nlp = spacy.load("en_core_web_sm")

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Function to extract text from a PDF resume
def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

# Function to preprocess text (tokenize, lemmatize, remove stopwords)
def preprocess_text(text):
    doc = nlp(text.lower())
    tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    return " ".join(tokens)

# Function to compute similarity between job description and resumes
def rank_resumes(job_description, resume_files):
    # Preprocess job description
    job_desc_processed = preprocess_text(job_description)
    
    # Initialize lists to store resume data
    resume_texts = []
    resume_names = []
    
    # Extract text from uploaded resumes
    for resume_file in resume_files:
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(resume_file.filename))
        resume_file.save(resume_path)
        resume_text = extract_text_from_pdf(resume_path)
        if resume_text:
            resume_texts.append(preprocess_text(resume_text))
            resume_names.append(resume_file.filename)
        os.remove(resume_path)  # Clean up after processing
    
    if not resume_texts:
        return None
    
    # Combine job description and resume texts for vectorization
    all_texts = [job_desc_processed] + resume_texts
    
    # Convert texts to TF-IDF vectors
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    
    # Compute cosine similarity between job description and each resume
    job_vector = tfidf_matrix[0]
    similarities = cosine_similarity(job_vector, tfidf_matrix[1:])[0]
    
    # Create a DataFrame with resume names and similarity scores
    results = pd.DataFrame({
        "Resume": resume_names,
        "Similarity_Score": similarities
    })
    
    # Sort resumes by similarity score in descending order
    results = results.sort_values(by="Similarity_Score", ascending=False)
    
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    job_description = request.form.get('jobDescription')
    resume_files = request.files.getlist('resumes')
    
    if not job_description or not resume_files:
        return jsonify({"error": "Job description and resumes are required"}), 400
    
    results = rank_resumes(job_description, resume_files)
    
    if results is None:
        return jsonify({"error": "No valid resumes processed"}), 400
    
    # Convert results to JSON
    results_json = results.to_dict(orient='records')
    return jsonify(results_json)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)