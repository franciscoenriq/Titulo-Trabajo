from werkzeug.security import generate_password_hash

# Reemplaza con la contraseña que quieras hashear
password_plana = 'contraseñasegura'
hash = generate_password_hash(password_plana)

print(hash)
