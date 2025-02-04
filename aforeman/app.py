from flask import Flask, render_template, Response, request, jsonify, session
from anthropic import Anthropic
from dotenv import load_dotenv
import os
import json
import base64
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = os.urandom(24)  # Required for session management

# Store file contents in memory
file_contents = {}

# Load environment variables
load_dotenv()
anthropic = Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    # Add the required beta header for PDF support
    default_headers={"anthropic-beta": "pdfs-2024-09-25"}
)

def encode_file_to_base64(file_path):
    """Convert file to base64 string"""
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Store file content in memory
            file_contents[filename] = encode_file_to_base64(file_path)
            return jsonify({'success': True, 'filename': filename})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Clean up the temporary file
            if os.path.exists(file_path):
                os.remove(file_path)

@app.route('/remove_file', methods=['POST'])
def remove_file():
    filename = request.json.get('filename')
    if filename in file_contents:
        del file_contents[filename]
        return jsonify({'success': True})
    return jsonify({'error': 'File not found'}), 404

@app.route('/stream', methods=['POST'])
def stream():
    data = request.json
    user_message = data.get('message', '')
    files = data.get('files', [])
    
    print(f"Received message request with files: {files}")
    print(f"Available files in memory: {list(file_contents.keys())}")
    
    # Prepare message content array
    content = []
    
    # Add file contents as documents
    for filename in files:
        secure_name = secure_filename(filename)
        if secure_name in file_contents:
            content.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": file_contents[secure_name]
                }
            })
            print(f"Added file content for: {secure_name}")
        else:
            print(f"File not found in memory: {secure_name}")
    
    # Add the text message
    content.append({
        "type": "text",
        "text": user_message
    })

    def generate():
        try:
            print("Sending message to Claude with content types:", [item["type"] for item in content])
            message = anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",  # Updated to latest model with PDF support
                max_tokens=4096,
                temperature=0.7,
                stream=True,
                messages=[{
                    "role": "user",
                    "content": content
                }]
            )

            for chunk in message:
                if chunk.type == "content_block_delta":
                    data = {
                        "text": chunk.delta.text,
                        "type": "content"
                    }
                    yield f"data: {json.dumps(data)}\n\n"

        except Exception as e:
            error_data = {
                "error": str(e),
                "type": "error"
            }
            print(f"Error in generate(): {str(e)}")
            yield f"data: {json.dumps(error_data)}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)