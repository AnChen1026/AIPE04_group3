from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints


# 只有空白的字串也算沒填
Required = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class TeacherIn(BaseModel):
    """老師個人資料。照片以外都必填（UIUX 回饋），填完才能建立課程。性別和帳號一樣只有男、女。"""

    name: Annotated[Required, Field(max_length=100)]
    gender: Literal["男", "女"]
    age: int = Field(ge=0, le=120)
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
    # 照片以外的欄位都填了沒；沒填完不能建立課程
    profile_complete: bool = False
