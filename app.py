from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
import sqlite3
from utils import predict_with_heatmap

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
HEATMAP_FOLDER = 'static/heatmaps'

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(HEATMAP_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['HEATMAP_FOLDER'] = HEATMAP_FOLDER

# -------------------- DB Initialization --------------------
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        email TEXT UNIQUE,
                        password TEXT)''')
    conn.commit()
    conn.close()

init_db()

# -------------------- Routes --------------------
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            flash("Passwords don't match")
            return redirect(url_for('signup'))

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            conn.close()
            flash("Account created successfully. Please log in.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already exists")
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = user[1]
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', user=session['user'])

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        flash("No image uploaded")
        return redirect(url_for('home'))

    image = request.files['image']
    if image.filename == '':
        flash("No selected file")
        return redirect(url_for('home'))

    # Save uploaded image
    filename = secure_filename(image.filename)
    uploaded_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(uploaded_image_path)

    # Perform prediction and generate heatmap
    #result, percentage, heatmap_path, precautions = predict_with_heatmap(uploaded_image_path)
    result, percentage, heatmap_path, precautions, uploaded_image = predict_with_heatmap(uploaded_image_path)  


    return render_template(
        'result.html',
        result=result,
        percentage=percentage,
        uploaded_image=f"uploads/{filename}",
        heatmap_image=heatmap_path if heatmap_path else "heatmaps/default_heatmap.jpg",
        precautions=precautions
    )

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
