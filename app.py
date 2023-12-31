import os
import random
import requests
import base64
import json
from flask import Flask, request, redirect, flash, get_flashed_messages
import boto3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024 # Maximum file size: 16GB
app.secret_key = os.getenv('SECRET_KEY')

s3 = boto3.client('s3', 
                  aws_access_key_id=os.getenv('S3_ACCESS_KEY_ID'),
                  aws_secret_access_key=os.getenv('S3_SECRET_ACCESS_KEY'),
                  region_name=os.getenv('S3_REGION'),
                  endpoint_url=os.getenv('S3_ENDPOINT_URL'))

bucket_name = os.getenv('S3_BUCKET_NAME')  # Replace with your S3 bucket name

def scanfile(file):
    SCAN_API_BASE_URL = os.getenv('SCAN_API_BASE_URL')
    SCAN_API_USERNAME = os.getenv('SCAN_API_USERNAME')
    SCAN_API_PASSWORD = os.getenv('SCAN_API_PASSWORD')
    
    random_number = str(random.randint(1000000, 9999999))
    url = f'{SCAN_API_BASE_URL}/GAMScanServer/v1/scans/cScanner/{random_number}'

    file.seek(0)  # reset file pointer to the beginning
    file_content = file.read()
    file_content_base64 = base64.b64encode(file_content).decode('utf-8')  # Encode to BASE64 and decode to string

    payload = {
        'Body': file_content_base64,
        'SourceURL': 'aHR0cDovLzAvZmlsZS9hYmMxMjMuZGF0',
    }
    
    headers = {'Content-Type': 'application/json'}

    # Get the basic auth username and password from environment variables


    response = requests.post(url, 
                             data=json.dumps(payload), 
                             headers=headers, 
                             auth=(SCAN_API_USERNAME, SCAN_API_PASSWORD))



    if response.status_code != 200:
        flash('File scanning failed due to server error.')
        return True  # Consider server error as scan failure
    
    json_response = response.json()

    if json_response.get('MalwareName'):
        flash('File is infected and cannot be accepted.')
        return True
    else:
        return False

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and scanfile(file) == False:
            filename = secure_filename(file.filename)
            file.seek(0)
            s3.upload_fileobj(file, bucket_name, filename)
            flash('File successfully uploaded and stored.')
            return redirect(request.url)

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    {}  <!-- Display the flash message here -->
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''.format('<br>'.join([f'<p style="color: red;">{message}</p>' for message in get_flashed_messages()]))

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')
