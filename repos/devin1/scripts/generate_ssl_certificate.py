import subprocess
import os
import datetime

CERT_DIR = "security/"
CERT_FILE = os.path.join(CERT_DIR, "certificate.crt")
KEY_FILE = os.path.join(CERT_DIR, "private_key.pem")

def generate_certificate():
    """
    Generates a self-signed SSL certificate and private key.
    """
    if not os.path.exists(CERT_DIR):
        os.makedirs(CERT_DIR)
        print(f"Created directory: {CERT_DIR}")

    print("Generating SSL certificate and private key...")
    command = [
        "openssl", "req", "-x509", "-nodes", "-days", "365",
        "-newkey", "rsa:2048",
        "-keyout", KEY_FILE,
        "-out", CERT_FILE,
        "-subj", "/C=US/ST=California/L=SanFrancisco/O=Devin/OU=AIProject/CN=localhost"
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Certificate generated: {CERT_FILE}")
        print(f"Private key saved: {KEY_FILE}")
    except FileNotFoundError:
        print("Error: OpenSSL not found. Please install OpenSSL to use this feature.")
    except subprocess.CalledProcessError as e:
        print(f"Error generating certificate: {e}")

def verify_certificate():
    """
    Verifies the generated SSL certificate.
    """
    print("Verifying SSL certificate...")
    if os.path.exists(CERT_FILE):
        expiration_date = subprocess.check_output(
            ["openssl", "x509", "-in", CERT_FILE, "-enddate", "-noout"]
        ).decode().strip().split("=")[1]
        print(f"Certificate is valid until: {expiration_date}")
    else:
        print("Certificate file not found.")

if __name__ == "__main__":
    print("SSL Certificate Management")
    print(f"Timestamp: {datetime.datetime.now()}")
    generate_certificate()
    verify_certificate()
