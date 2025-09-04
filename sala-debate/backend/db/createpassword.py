from werkzeug.security import generate_password_hash

# Reemplaza con la contraseña que quieras hashear
password_plana = '1234'
hash = generate_password_hash(password_plana)

print(hash)
