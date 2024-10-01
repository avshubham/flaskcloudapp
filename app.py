from flask import Flask, render_template, request, flash
import boto3
from werkzeug.utils import secure_filename
from trp import Document

app = Flask(__name__)

ACCESS_KEY_ID = "AKIA4VRC4PXZOY6XFF7E"
ACCESS_SECRET_KEY = "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"
BUCKET_NAME = "minicloudpro"

s3 = boto3.client('s3',
                  aws_access_key_id=ACCESS_KEY_ID,
                  aws_secret_access_key=ACCESS_SECRET_KEY
)

textract = boto3.client('textract',
                        aws_access_key_id=ACCESS_KEY_ID,
                        aws_secret_access_key=ACCESS_SECRET_KEY,
                        region_name='us-east-1'
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        img = request.files['file']
        if img:
            filename = secure_filename(img.filename)
            img.save(filename)
            s3.upload_file(Filename=filename, Bucket=BUCKET_NAME, Key=filename)
            flash("Upload Done ! ", 'success')
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    text = []
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        if 'Contents' in response:
            obj = response['Contents'][0]
            document_name = obj['Key']

            # Download the document from S3
            s3.download_file(BUCKET_NAME, document_name, document_name)

            # Call Amazon Textract
            with open(document_name, "rb") as document:
                response = textract.analyze_document(
                    Document={
                        'Bytes': document.read(),
                    },
                    FeatureTypes=["FORMS"]
                )

            doc = Document(response)
            for page in doc.pages:
                for field in page.form.fields:
                    text.append((field.key, field.value))

        else:
            flash("No objects found in the bucket.", 'warning')
    except Exception as e:
        flash(f"Error: {str(e)}", 'danger')

    return render_template('index.html', text=text)

if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.run(debug=True)
