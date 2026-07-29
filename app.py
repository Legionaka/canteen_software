from flask import Flask, render_template, request, redirect, url_for
from routes.student import student_bp
from routes.staff import staff_bp
from routes.admin import admin_bp
from routes.auth import auth_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'import secret key from .env(Placeholder - ammara)'

app.register_blueprint(student_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)

@app.route('/')
def index():
    return render_template('base.html')

if __name__ == '__main__':
    app.run(debug=True)