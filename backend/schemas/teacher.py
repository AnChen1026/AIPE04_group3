from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints


# 只有空白的字串也算沒填
Required = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class TeacherIn(BaseModel):
    """老師的個人資料頁：帳號資料（姓名、性別、手機、生日）和介紹一起存。照片以外都必填，填完才能建立課程。
    學生看到的性別就是帳號性別；年齡不再填（UIUX 回饋）。"""

    name: Annotated[Required, Field(max_length=100)]
    sex: Literal["male", "female"]
    phone_number: str = Field(pattern=r"^09\d{8}$")
    birthdate: date
    seniority: int = Field(ge=0, le=80)
    expertise: Annotated[Required, Field(max_length=200)]
    short_intros: Annotated[Required, Field(max_length=200)]
    teaching_city: Annotated[Required, Field(max_length=100)]
    teaching_district: Annotated[Required, Field(max_length=100)]
    target_learning: Annotated[Required, Field(max_length=255)]
    teaching_method: Annotated[Required, Field(max_length=255)]
    teaching_style: Annotated[Required, Field(max_length=100)]

    status: str = "active"


class TeacherProfileResponse(BaseModel):
    """老師個人資料。照片只給網址，不給伺服器上的檔案路徑。"""

    id: str
    user_id: str
    name: str
    gender: str
    age: int | None = None
    seniority: int | None = None
    expertise: str | None = None
    short_intros: str | None = None
    teaching_city: str | None = None
    teaching_district: str | None = None
    target_learning: str | None = None
    teaching_method: str | None = None
    teaching_style: str | None = None
    status: str
    photo_url: str | None = None
    # 帳號資料，同一頁一起顯示與修改
    email: str | None = None
    sex: str | None = None
    phone_number: str | None = None
    birthdate: date | None = None
    # 照片以外的欄位都填了沒；沒填完不能建立課程
    profile_complete: bool = False
