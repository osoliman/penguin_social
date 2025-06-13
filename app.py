from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///penguin_social.db'

# Update the upload folder path to be absolute
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Ensure the uploads directory is writable
try:
    os.chmod(app.config['UPLOAD_FOLDER'], 0o777)
except:
    pass  # Ignore if we can't change permissions

db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500))
    media_type = db.Column(db.String(10))  # 'image' or 'voice'
    media_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/post/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        content = request.form.get('content')
        media_type = request.form.get('media_type')
        
        if 'media' not in request.files:
            flash('No file selected')
            return redirect(request.url)
            
        file = request.files['media']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
            
        if file:
            # Create a safe filename
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
            # Ensure the filename is safe
            filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
            
            # Save the file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Ensure the file is readable
            try:
                os.chmod(file_path, 0o644)
            except:
                pass  # Ignore if we can't change permissions
            
            post = Post(
                content=content,
                media_type=media_type,
                media_path=filename
            )
            db.session.add(post)
            db.session.commit()
            
            return redirect(url_for('home'))
            
    return render_template('new_post.html')

@app.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    content = request.form.get('content')
    if content:
        comment = Comment(content=content, post_id=post_id)
        db.session.add(comment)
        db.session.commit()
    return redirect(url_for('home'))

# This is the application factory for PythonAnywhere
application = app

if __name__ == '__main__':
    app.run() 