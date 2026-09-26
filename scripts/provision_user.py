"""Provisiona o primeiro usuário sem expor cadastro público."""
import argparse
from getpass import getpass
from database.connection import SessionLocal
from services import provision_user

def main() -> None:
    parser = argparse.ArgumentParser(description="Provisiona um usuário do Aurora Finance.")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    password = getpass("Senha: ")
    if password != getpass("Confirme a senha: "):
        raise SystemExit("As senhas não coincidem.")
    with SessionLocal.begin() as session:
        user = provision_user(session, name=args.name, email=args.email, password=password)
        print(f"Usuário provisionado: {user.email}")

if __name__ == "__main__":
    main()
