from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from workflow import app_workflow
import os
from utils import Utils

app = Flask(__name__)
CORS(app)

utils = Utils()

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    # Handling PDF upload (using helper function)
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file part in the request"}), 400

    filename = file.filename
    temp_path = os.path.join("/tmp", filename)
    file.save(temp_path)

    try:
        message = utils.upload_pdf_to_blob(temp_path, filename)
        os.remove(temp_path)
        return jsonify({"message": message, "filename": filename}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/invoke", methods=["POST"])
def invoke_workflow():
    data = request.json
    if not data or "user_input" not in data:
        return jsonify({"error": "user_input is required"}), 400

    result = app_workflow.invoke(data)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
