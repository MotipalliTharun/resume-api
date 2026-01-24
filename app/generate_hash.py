from passlib.context import CryptContext
import sys

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate(password: str):
    hashed = pwd_context.hash(password)
    print(f"\nPassword: {password}")
    print(f"Bcrypt Hash: {hashed}\n")
    print("Set this as APP_PASSWORD_HASH in your environment variables or config.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate(sys.argv[1])
    else:
        print("Usage: python generate_hash.py <password>")
