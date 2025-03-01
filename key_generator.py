from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Generate a new RSA private key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,  # You can increase this size (e.g., 3072 or 4096) for more security
)

# Serialize and write the private key to a file (optional)
with open("private_key.pem", "wb") as priv_file:
    priv_file.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()  # or use a password-based encryption
        )
    )

# Extract the public key from the private key
public_key = private_key.public_key()

# Serialize and write the public key to a file
with open("public_key.pem", "wb") as pub_file:
    pub_file.write(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )

print("Public key saved to public_key.pem")
