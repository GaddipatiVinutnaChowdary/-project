"""Break-glass administrator recovery from the machine that hosts the app."""
from __future__ import annotations

import argparse
import getpass

from sqlalchemy import func, select

import server


def main() -> int:
    parser = argparse.ArgumentParser(description="Recover or bootstrap campus administrator access.")
    parser.add_argument("--allow-production", action="store_true",
                        help="Permit a break-glass password change in APP_ENV=production.")
    parser.add_argument("--reactivate", action="store_true",
                        help="Reactivate the specified existing administrator account.")
    parser.add_argument("--bootstrap", action="store_true",
                        help="Create an administrator only when no active administrator exists.")
    args = parser.parse_args()
    if server.APP_ENV == "production" and not args.allow_production:
        parser.error("APP_ENV=production; use --allow-production only in an approved recovery window.")

    email = input("Administrator email: ").strip().lower()
    if not email:
        print("An administrator email is required.")
        return 2

    with server.SessionLocal() as db:
        user = db.scalar(select(server.CampusUser).where(server.CampusUser.email == email))
        if user and user.role != "admin":
            print("That email belongs to a non-administrator account; no changes were made.")
            return 2

        if user:
            if not user.active and not args.reactivate:
                print("This administrator is disabled. Use --reactivate only if reactivation is authorized.")
                return 2
            action = "RESET"
        else:
            active_admins = db.scalar(select(func.count(server.CampusUser.id)).where(
                server.CampusUser.role == "admin", server.CampusUser.active.is_(True))) or 0
            if active_admins or not args.bootstrap:
                print("No matching administrator. Create one only with --bootstrap when no active administrator exists.")
                return 2
            action = "CREATE"

        if input(f"Type {action} {email} to continue: ").strip() != f"{action} {email}":
            print("Confirmation did not match; no changes were made.")
            return 2

        password = getpass.getpass("New administrator password (12+ characters): ")
        if password != getpass.getpass("Repeat new password: "):
            print("Passwords did not match; no changes were made.")
            return 2
        if len(password) < 12:
            print("Password must be at least 12 characters; no changes were made.")
            return 2

        if user is None:
            name = input("Administrator full name: ").strip()
            if len(name) < 2:
                print("Name must be at least two characters; no changes were made.")
                return 2
            user = server.CampusUser(email=server.normalize_email(email), full_name=name,
                                     password_hash=server.password_hash(password), role="admin", active=True)
            db.add(user)
            db.flush()
            audit_action = "auth.local_admin_bootstrap"
        else:
            user.password_hash = server.password_hash(password)
            if args.reactivate:
                user.active = True
            audit_action = "auth.local_admin_password_recovery"

        for session_row in db.scalars(select(server.AuthSession).where(
                server.AuthSession.user_id == user.id, server.AuthSession.revoked_at.is_(None))).all():
            session_row.revoked_at = server.utcnow()
        server.audit(db, None, audit_action, "administrator", user.id,
                     {"operator_channel": "local_cli", "reactivated": bool(args.reactivate)})
        db.commit()
        print(f"Administrator access is ready for {user.email}. Sign in at the campus staff URL.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
