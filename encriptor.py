from cryptography.fernet import Fernet


def key_create():
    key = Fernet.generate_key()
    return key


def key_write(key, key_name):
    with open(key_name, 'wb') as mykey:
        mykey.write(key)


def key_load(key_name):
    with open(key_name, 'rb') as mykey:
        key = mykey.read()
    return key


def file_encrypt(key, original_file, encrypted_file):
    f = Fernet(key)
    with open(original_file, 'rb') as file:
        original = file.read()
    encrypted = f.encrypt(original)
    with open(encrypted_file, 'wb') as file:
        file.write(encrypted)


def file_decrypt(key, encrypted_file, decrypted_file):
    f = Fernet(key)
    with open(encrypted_file, 'rb') as file:
        encrypted = file.read()
    decrypted = f.decrypt(encrypted)
    decrypted = decrypted.decode("utf-8")
    return decrypted


# if __name__ == '__main__':
#    mykey = key_create()
#    key_write(mykey, "mykey.key")
#    loaded_key = key_load('mykey.key')
#    aux = file_decrypt(loaded_key, 'sansw.conf', 'sansw.conf')
#    print(aux)
#    file_encrypt(loaded_key, 'ftp_credentials.conf', 'ftp_credentials.conf')
