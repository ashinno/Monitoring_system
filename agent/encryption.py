import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from config import Config

class Encryptor:
    def __init__(self, key_hex=None):
        if key_hex:
            self.key = bytes.fromhex(key_hex)
        else:
            # Fallback to config or generate random if not provided (though for comms we need shared key)
            # Ensuring key is 32 bytes for AES-256
            self.key = Config.ENCRYPTION_KEY.encode('utf-8')[:32].ljust(32, b'0')
            
        self.aesgcm = AESGCM(self.key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypts plaintext using AES-256-GCM.
        Returns: base64 encoded string containing nonce + ciphertext + tag
        """
        nonce = os.urandom(12) # NIST recommended nonce size
        data = plaintext.encode('utf-8')
        
        # encrypt() returns ciphertext + tag
        ciphertext = self.aesgcm.encrypt(nonce, data, None)
        
        # Combine nonce + ciphertext (tag is already at end of ciphertext in this lib implementation? 
        # Wait, AESGCM.encrypt returns ciphertext + tag appended.
        # We need to prepend nonce to transport it.
        combined = nonce + ciphertext
        return base64.b64encode(combined).decode('utf-8')

    def decrypt(self, encrypted_b64: str) -> str:
        """
        Decrypts base64 encoded string.
        """
        try:
            combined = base64.b64decode(encrypted_b64)
            nonce = combined[:12]
            ciphertext = combined[12:]
            
            plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        except Exception as e:
            print(f"Decryption failed: {e}")
            return None

if __name__ == "__main__":
    # Test
    e = Encryptor()
    original = "This is a secret keystroke log."
    encrypted = e.encrypt(original)
    print(f"Encrypted: {encrypted}")
    decrypted = e.decrypt(encrypted)
    print(f"Decrypted: {decrypted}")
    assert original == decrypted
    print("Encryption Test Passed")
