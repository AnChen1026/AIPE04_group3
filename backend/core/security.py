"""帳號安全相關工具。"""

from argon2 import PasswordHasher

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """把明文密碼轉成可安全保存的 Argon2 雜湊。"""
    return password_hasher.hash(password)
