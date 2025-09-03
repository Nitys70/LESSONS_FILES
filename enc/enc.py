def add_secret(jpg_file, secret, out_file):
    with open(jpg_file, "rb") as f:
        data = f.read()

    # Убираем маркер конца (FFD9)
    if data[-2:] == b"\xff\xd9":
        data = data[:-2]

    # Добавляем маркер + секрет + обратно конец
    new_data = data + b"\nSECRET_START\n" + secret.encode() + b"\nSECRET_END\n" + b"\xff\xd9"

    with open(out_file, "wb") as f:
        f.write(new_data)


# Извлечение пароля
def get_secret(jpg_file):
    with open(jpg_file, "rb") as f:
        data = f.read()

    start = data.find(b"SECRET_START")
    end = data.find(b"SECRET_END")

    if start != -1 and end != -1:
        secret = data[start+len(b"SECRET_START"):end]
        return secret.decode()
    else:
        return None


# Пример использования
add_secret("image.jpg", "mypassword123", "image_secret.jpg")
print(get_secret("image_secret.jpg"))