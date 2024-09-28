import requests
import os

file_path = "cleaned_reviews.csv"  
url = "http://127.0.0.1:5000/analyze_sentiment"


if not os.path.exists(file_path):
    print(f"Error: File '{file_path}' not found. Please run the preprocessing script first.")
    exit(1)

try:
    with open(file_path, 'rb') as file:
        files = {'file': (os.path.basename(file_path), file, 'text/csv')}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        print("Sentiment Analysis Results:")
        print(f"Positive: {result['positive']:.2f}")
        print(f"Negative: {result['negative']:.2f}")
        print(f"Neutral: {result['neutral']:.2f}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

except requests.exceptions.RequestException as e:
    print(f"Error connecting to the API: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
