"""帳號安全相關工具。"""

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """把明文密碼轉成可安全保存的 Argon2 雜湊。"""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """確認明文密碼是否符合資料庫中的 Argon2 雜湊。"""
    try:
        return password_hasher.verify(password_hash, password)
    except VerificationError:
        return False
