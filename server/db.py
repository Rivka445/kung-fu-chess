"""SQLite-backed accounts: username/password auth (auto-register) + ELO rating."""

import hashlib
import os
import secrets
import sqlite3

from server.elo import apply as elo_apply

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "chess.db")
STARTING_RATING = 1200
_PBKDF2_ITERATIONS = 100_000


class AuthError(Exception):
    pass


def _hash_password(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), _PBKDF2_ITERATIONS
    ).hex()


def init_db(path: str = DEFAULT_DB_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username      TEXT PRIMARY KEY,
                salt          TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                rating        INTEGER NOT NULL DEFAULT 1200
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def authenticate_or_register(username: str, password: str, path: str = DEFAULT_DB_PATH) -> int:
    """
    Look up `username`. If it doesn't exist yet, create the account with
    `password` and the starting rating (auto-register). If it exists, verify
    `password` against the stored hash — raises AuthError on mismatch.
    Returns the account's current rating either way.
    """
    init_db(path)
    conn = sqlite3.connect(path)
    try:
        row = conn.execute(
            "SELECT salt, password_hash, rating FROM users WHERE username = ?", (username,)
        ).fetchone()

        if row is None:
            salt = secrets.token_hex(16)
            password_hash = _hash_password(password, salt)
            conn.execute(
                "INSERT INTO users (username, salt, password_hash, rating) VALUES (?, ?, ?, ?)",
                (username, salt, password_hash, STARTING_RATING),
            )
            conn.commit()
            return STARTING_RATING

        salt, stored_hash, rating = row
        if _hash_password(password, salt) != stored_hash:
            raise AuthError("wrong password")
        return rating
    finally:
        conn.close()


def get_rating(username: str, path: str = DEFAULT_DB_PATH) -> int:
    init_db(path)
    conn = sqlite3.connect(path)
    try:
        row = conn.execute("SELECT rating FROM users WHERE username = ?", (username,)).fetchone()
        if row is None:
            raise AuthError(f"unknown user: {username}")
        return row[0]
    finally:
        conn.close()


def update_ratings(
    white_username: str, black_username: str, result: str, path: str = DEFAULT_DB_PATH
) -> tuple[int, int]:
    """
    Apply an ELO update for one finished game and persist it.
    `result` is from white's perspective: "white", "black", or "draw".
    Returns (new_white_rating, new_black_rating).
    """
    score_white = {"white": 1.0, "black": 0.0, "draw": 0.5}[result]
    init_db(path)
    conn = sqlite3.connect(path)
    try:
        white_rating = conn.execute(
            "SELECT rating FROM users WHERE username = ?", (white_username,)
        ).fetchone()[0]
        black_rating = conn.execute(
            "SELECT rating FROM users WHERE username = ?", (black_username,)
        ).fetchone()[0]

        new_white, new_black = elo_apply(white_rating, black_rating, score_white)

        conn.execute("UPDATE users SET rating = ? WHERE username = ?", (new_white, white_username))
        conn.execute("UPDATE users SET rating = ? WHERE username = ?", (new_black, black_username))
        conn.commit()
        return new_white, new_black
    finally:
        conn.close()
