from encryption import Encryptor


def test_encrypt_decrypt_roundtrip_with_fixed_key():
    e = Encryptor(key_hex="00" * 32)
    plaintext = "secret"
    encrypted = e.encrypt(plaintext)
    assert encrypted != plaintext
    decrypted = e.decrypt(encrypted)
    assert decrypted == plaintext


def test_decrypt_invalid_payload_returns_none():
    e = Encryptor(key_hex="00" * 32)
    assert e.decrypt("not-base64") is None

