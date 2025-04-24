from flask import Flask, request, send_from_directory, jsonify

import os
import markdown
import time
from jinja2 import Environment, PackageLoader, select_autoescape
import re
import uuid
import requests
# import datatime
app = Flask(__name__)

# 配置文件夹路径
UPLOAD_FOLDER = './files'
OUTPUT_FOLDER = 'data'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# 确保文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# def generate_timestamp():
#     timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
#     return f"- 生成时间:{timestamp}"

def get_public_ip():
    try:
        # 使用外部服务获取公网 IP
        response = requests.get('https://api.ipify.org').text
        return response.strip()
    except:
        return None
    
host_ip = get_public_ip()


@app.route('/upload_html',methods=['POST'])
def upload_html():
    # host_ip = get_public_ip()
    file_suffix = str(uuid.uuid4())[:8]

    # Check if the request contains JSON with file_name and file_content
    if request.is_json:
        json_data = request.get_json()
        if 'file_name' in json_data and 'file_content' in json_data:
            file_name = json_data['file_name']
            content = json_data['file_content']
            
            # Remove .html extension if present
            if file_name.endswith('.html'):
                filename = file_name[:-5]
            else:
                filename = file_name
        else:
            return jsonify({"error": "JSON must contain file_name and file_content fields"}), 400
    # Check if the request contains a file upload
    elif 'file' in request.files:
        file = request.files['file']
        
        # Get the original filename
        original_filename = file.filename
        
        # Remove .html extension if present
        if original_filename.endswith('.html'):
            filename = original_filename[:-5]
        else:
            filename = original_filename
            
        # Get content from file
        content = file.read().decode('utf-8')
    # Handle direct content upload as fallback
    else:
        # Direct content upload
        content = request.get_data(as_text=True)
        if content is None:
            return jsonify({"error": "Invalid input"}), 400
            
        # Use a timestamp as filename since no original filename is available
        filename = f"html_content"
    
    filename = f"{filename}_{file_suffix}"

    # Save the HTML content directly without modifications
    with open(os.path.join(OUTPUT_FOLDER, f"{filename}.html"), "w+", encoding='utf-8') as f:
        f.write(content)
    
    return jsonify(
        {"url":
         f"http://{host_ip}:5006/get_html/{filename}.html"}), 200
    
@app.route('/upload_markdown', methods=['POST'])
def upload_markdown():
    
    file_suffix = str(uuid.uuid4())[:8]
    # Check if the request contains JSON with file_name and file_content
    if request.is_json:
        json_data = request.get_json()
        if 'file_name' in json_data and 'file_content' in json_data:
            file_name = json_data['file_name']
            content = json_data['file_content']
            
            # Remove .md extension if present
            if file_name.endswith('.md'):
                filename = file_name[:-3]
            else:
                filename = file_name
        else:
            return jsonify({"error": "JSON must contain file_name and file_content fields"}), 400
    # Check if the request contains a file upload
    elif 'file' in request.files:
        file = request.files['file']
        
        # Get the original filename
        original_filename = file.filename
        
        # Remove .md extension if present
        if original_filename.endswith('.md'):
            filename = original_filename[:-3]
        else:
            filename = original_filename
            
        # Get content from file
        content = file.read().decode('utf-8')
    # Handle direct content upload as fallback
    else:
        content = request.get_data(as_text=True)
        if content is None:
            return jsonify({"error": "Invalid input"}), 400
        
        # Use UUID for filename when no name is provided
        filename = str(uuid.uuid4())
    
   
    html_content = markdown.markdown(content)
    complete_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Markdown Rendered</title>
</head>
<body>
    {html_content}
</body>
</html>
""" 
    filename = f"{filename}_{file_suffix}"
    with open(os.path.join(OUTPUT_FOLDER, f"{filename}.html"),
              "w+",
              encoding='utf-8') as f:  # create final file
        f.write(complete_html)

    return jsonify(
        {"url":
         f"http://{host_ip}:5006/get_html/{filename}.html"}), 200

@app.route('/',methods=['GET'])
def ping():
    return jsonify({"message": "ok"}), 200

@app.route('/get_html/<filename>', methods=['GET'])
def get_html(filename):
    if not filename.endswith('.html'):
        filename += '.html'

    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True, port=5006, host='0.0.0.0')
