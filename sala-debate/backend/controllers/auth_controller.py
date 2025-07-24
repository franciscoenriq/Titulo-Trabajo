# controllers/auth_controller.py

from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from models.models import  *


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    db = Session()
    try:
        user = db.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            return jsonify({
                'message': 'Login exitoso',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'rol': user.role.value
                }
            }), 200
        else:
            return jsonify({'error': 'Credenciales inválidas'}), 401
    finally:
        db.close()

@auth_bp.route('/logout', methods=['POST'])
def logout():
    # En una API REST, el "logout" se suele manejar en el frontend
    # borrando el token o la sesión del lado cliente.
    return jsonify({'message': 'Logout exitoso (cliente debe eliminar token)'}), 200
