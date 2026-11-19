"""Provision credentials from a trusted server terminal."""

import argparse
from getpass import GetPassWarning, getpass
from typing import Literal
import warnings

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from server.auth import PASSWORD_HASHER
from server.database import get_engine
from server.models import User
from server.schemas import AuthEmail, StudentRegistration


def provision_account(
    db: Session,
    *,
    email: str,
    password: str,
    role: Literal["Student", "Professor"],
    name: str | None,
) -> None:
    email = AuthEmail(email=email).email
    user = db.scalar(select(User).where(User.email == email).with_for_update())
    if user is not None and user.password_hash is not None:
        raise ValueError("The account already has credentials")
    if user is None and not name:
        raise ValueError("--name is required when creating an account")

    details = StudentRegistration(
        name=user.name if user else name, email=email, password=password
    )
    if user is None:
        user = User(name=details.name, email=details.email)
        db.add(user)
    user.account_role = role
    user.password_hash = PASSWORD_HASHER.hash(details.password.get_secret_value())
    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", required=True, choices=["Student", "Professor"])
    parser.add_argument("--name", help="Required for a new account")
    args = parser.parse_args()

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", GetPassWarning)
            password = getpass("Password (15–128 characters): ")
            confirmation = getpass("Confirm password: ")
    except (GetPassWarning, EOFError):
        parser.exit(1, "A terminal with hidden password input is required.\n")
    if password != confirmation:
        parser.exit(1, "Passwords do not match.\n")

    try:
        with Session(get_engine()) as db:
            provision_account(
                db, email=args.email, password=password, role=args.role, name=args.name
            )
    except ValidationError:
        parser.exit(1, "Provide a valid email, name, and password of 15–128 characters.\n")
    except ValueError as error:
        parser.exit(1, f"{error}\n")
    except IntegrityError:
        parser.exit(1, "Account provisioning conflicted with an existing record.\n")

    print("Account credentials provisioned.")


if __name__ == "__main__":
    main()
