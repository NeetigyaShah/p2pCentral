from flask import Flask, request, jsonify, send_from_directory
from models import db, File
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize database
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return "No file provided", 400
    
    f = request.files["file"]
    if f.filename == '':
        return "No file selected", 400
        
    path = os.path.join(app.config["UPLOAD_FOLDER"], f.filename)
    f.save(path)
    
    # Check if file already exists in database
    existing_file = File.query.filter_by(name=f.filename).first()
    if not existing_file:
        file = File(name=f.filename, path=path)
        db.session.add(file)
        db.session.commit()
    
    return "File uploaded successfully", 201

@app.route("/files")
def files():
    return jsonify([f.name for f in File.query.all()])

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

@app.route("/")
def home():
    return "File Server is running!"

if __name__ == "__main__":
    print("Starting Flask server on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)