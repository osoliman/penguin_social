from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
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

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

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
    image_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

# Create all database tables
with app.app_context():
    db.drop_all()  # Drop all existing tables
    db.create_all()  # Create new tables

@app.route('/')
def home():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/post/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        content = request.form.get('content')
        
        if 'image' not in request.files:
            flash('No image selected')
            return redirect(request.url)
            
        file = request.files['image']
        if file.filename == '':
            flash('No image selected')
            return redirect(request.url)
            
        if file:
            if not allowed_file(file.filename):
                flash('Please upload an image file (png, jpg, jpeg, or gif)')
                return redirect(request.url)
            
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
                image_path=filename
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

@app.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Delete the associated file
    if post.image_path:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], post.image_path)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass  # Ignore if we can't delete the file
    
    # Delete the post and its comments
    db.session.delete(post)
    db.session.commit()
    
    flash('Post deleted successfully!')
    return redirect(url_for('home'))

# This is the application factory for PythonAnywhere
application = app

if __name__ == '__main__':
    app.run() 