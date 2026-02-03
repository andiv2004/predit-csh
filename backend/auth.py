from functools import wraps
from flask import request, jsonify

# Credențialele - poți schimba USERNAME și PASSWORD
USERNAME = "admin"
PASSWORD = "csh2025"

def check_auth(username, password):
    """Verifică dacă credențialele sunt corecte"""
    return username == USERNAME and password == PASSWORD

def authenticate():
    """Returnează eroare de autentificare"""
    return jsonify({'message': 'Authentication required'}), 401

def require_auth(f):
    """Decorator pentru a proteja rutele cu HTTP Basic Auth"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated_function
