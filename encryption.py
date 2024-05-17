import random
import string

chars = " " + string.punctuation + string.digits + string.ascii_letters
chars = list(chars)
key = chars.copy()

random.shuffle(key)

def get_key():
    return ''.join(key)

def set_key(key1):
    global key
    key = key1
#ENCRYPT
def encrypt(message):
    plain_text = str(message)
    cipher_text = ""

    for letter in plain_text:
        index = chars.index(letter)
        cipher_text += key[index]

    print(f"original message : {plain_text}")
    print(f"encrypted message: {cipher_text}")
    return cipher_text

#DECRYPT
def decrypt(message):
    cipher_text = str(message)
    plain_text = ""

    for letter in cipher_text:
        index = key.index(letter)
        plain_text += chars[index]

    print(f"encrypted message: {cipher_text}")
    print(f"original message : {plain_text}")
    return plain_text
