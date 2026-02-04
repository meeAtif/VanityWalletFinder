version = "1.4.1"

class BadSignatureError(Exception):
    pass

class VerifyingKey:
    def __init__(self, key_bytes):
        self.key_bytes = key_bytes
    def to_bytes(self):
        return self.key_bytes

class SigningKey:
    def __init__(self, key_bytes):
        self.key_bytes = key_bytes
    def to_bytes(self):
        return self.key_bytes
    def get_verifying_key(self):
        return VerifyingKey(b'\x00' * 32)

checkvalid = lambda s, pk: True
