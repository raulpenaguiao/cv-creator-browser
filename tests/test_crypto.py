def test_encrypt_decrypt_roundtrip(app):
    with app.app_context():
        from app.services.crypto_service import decrypt_api_key, encrypt_api_key

        key = 'sk-test-1234567890abcdef'
        encrypted = encrypt_api_key(key)
        assert encrypted != key.encode()
        assert isinstance(encrypted, bytes)

        decrypted = decrypt_api_key(encrypted)
        assert decrypted == key


def test_different_keys_produce_different_ciphertext(app):
    with app.app_context():
        from app.services.crypto_service import encrypt_api_key

        enc1 = encrypt_api_key('key-one')
        enc2 = encrypt_api_key('key-two')
        assert enc1 != enc2
