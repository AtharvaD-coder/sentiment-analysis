import os
import json
import re
import csv
from flask import Flask, request, jsonify, render_template, send_from_directory
import pandas as pd
import requests
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def remove_emojis(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', str(text))

def preprocess_excel(file_path):
    df = pd.read_excel(file_path, header=None, names=['Review'])
    df['Review'] = df['Review'].apply(remove_emojis)
    
    # Create a CSV file path
    csv_file_path = os.path.splitext(file_path)[0] + '.csv'
    
    # Save to CSV
    df.to_csv(csv_file_path, index=False, quoting=csv.QUOTE_ALL)
    
    return csv_file_path

def analyze_sentiment(text):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {
                "role": "system",
                "content": "You are a sentiment analysis expert. Analyze the following reviews and provide overall scores for positive, negative, and neutral sentiments. The scores should add up to 1. Respond with only the JSON object containing the scores."
            },
            {
                "role": "user",
                "content": f"Analyze the sentiment of these reviews:\n\n{text}"
            }
        ],
        "temperature": 0.1
    }
    response = requests.post(GROQ_API_URL, json=data, headers=headers)
    response.raise_for_status()
    result = response.json()
    content = result['choices'][0]['message']['content']
    try:
        sentiment_scores = json.loads(content)
    except json.JSONDecodeError:
        # If JSON parsing fails, try to extract the scores using regex
        pattern = r'"positive":\s*([\d.]+).*"negative":\s*([\d.]+).*"neutral":\s*([\d.]+)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            sentiment_scores = {
                "positive": float(match.group(1)),
                "negative": float(match.group(2)),
                "neutral": float(match.group(3))
            }
        else:
            raise ValueError("Unable to parse sentiment scores from LLM response")
    return sentiment_scores

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_reviews():
    print("Received request to /analyze")
    print(f"Request files: {request.files}")
    print(f"Request form: {request.form}")
    
    if 'file' not in request.files:
        print("No file part in the request")
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    print(f"Received file: {file.filename}")
    
    if file.filename == '':
        print("No selected file")
        return jsonify({"error": "No selected file"}), 400
    
    if not file.filename.endswith('.xlsx'):
        print("File is not an XLSX file")
        return jsonify({"error": "Please upload an XLSX file"}), 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    print(f"File saved to {file_path}")
    
    try:
        csv_file_path = preprocess_excel(file_path)
        print(f"Excel file preprocessed and saved as CSV: {csv_file_path}")
    except Exception as e:
        print(f"Error processing XLSX file: {str(e)}")
        return jsonify({"error": f"Error processing XLSX file: {str(e)}"}), 400
    
    # Read the CSV file
    with open(csv_file_path, 'r') as csv_file:
        reviews = csv_file.readlines()
    
    print(f"Number of reviews: {len(reviews)}")
    
    # Join all reviews into a single string
    all_reviews = "\n".join(reviews)
    
    try:
        print("Sending reviews to sentiment analysis")
        sentiment = analyze_sentiment(all_reviews)
        print(f"Sentiment analysis result: {sentiment}")
    except Exception as e:
        print(f"Error analyzing sentiment: {str(e)}")
        return jsonify({"error": f"Error analyzing sentiment: {str(e)}"}), 500
    
    # Clean up temporary files
    os.remove(file_path)
    os.remove(csv_file_path)
    print("Temporary files removed")
    
    print(f"Final result: {sentiment}")
    return jsonify(sentiment)

@app.route('/test_upload', methods=['POST'])
def test_upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify({"message": "File uploaded successfully", "filename": filename}), 200
    return jsonify({"error": "Invalid file type"}), 400

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'xlsx'}

if __name__ == '__main__':
    app.run(debug=True)