import requests
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS  # To handle CORS

app = Flask(__name__)
CORS(app)  # Enable CORS

# Replace with your actual API key
API_KEY = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
GEMINI_API_URL = XXXXXXXXXXXXXXXXXXXXXXXXXXX

def get_gemini_response(user_message):
    # Data structure for Google Gemini API
    data = {
        "contents": [
            {
                "parts": [
                    {"text": user_message}
                ]
            }
        ]
    }

    headers = {'Content-Type': 'application/json'}

    # Send POST request to Gemini API
    response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(data))

    # Log the raw response for debugging
    print("Raw response status code:", response.status_code)
    print("Raw response text:", response.text)  # Log the full response text

    # Check if the request was successful
    if response.status_code == 200:
        response_json = response.json()
        print("API Response:", response_json)  # Log the response for debugging
        
        # Extract the response text from the new structure
        candidates = response_json.get('candidates', [])
        if candidates and isinstance(candidates, list):
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if parts and isinstance(parts, list):
                return parts[0].get('text', 'No response text found.')
        
        return "Response structure is different than expected."
    
    else:
        print(f"Error: {response.status_code}, Response: {response.text}")  # Log the error
        return f"Error: {response.status_code}, {response.text}"

# Serve the HTML file from the same directory as app.py
@app.route('/')
def serve_html():
    return send_from_directory('.', 'index.html')

# Handle chatbot requests
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    
    # Check if message was received
    print(f"Received message: {user_message}")
    
    # Get the response from the Gemini API
    chatbot_reply = get_gemini_response(user_message)
    
    # Log the reply
    print(f"Chatbot reply: {chatbot_reply}")
    
    return jsonify({"reply": chatbot_reply})

if __name__ == '__main__':
    app.run(debug=True)
