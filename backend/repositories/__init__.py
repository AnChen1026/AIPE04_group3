# 資料庫存取，放查詢、新增、修改、刪除資料的相關程式。
# 專門跟資料庫拿資料或存資料。

from backend.repositories.user import add_user, get_user_by_email

__all__ = ["add_user", "get_user_by_email"]