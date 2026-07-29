from flask import session , redirect , url_for
import functools

def login_required(i):
    @functools.wraps(i)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        else:
            return i(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(i):
        @functools.wraps(i)
        def decorated_function(*args, **kwargs):
            if session['role'] not in roles :
                return redirect(url_for('auth.login'))
            else:
                return i(*args, **kwargs)
        return decorated_function
    return decorator