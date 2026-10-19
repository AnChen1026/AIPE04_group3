from pydantic import BaseModel, Field


class TeacherIn(BaseModel):
    """老師個人資料。只有姓名、性別必填；授課方式、地區等可以在每門課再設定。"""

    name: str = Field(min_length=1, max_length=100)
    gender: str = Field(min_length=1, max_length=20)
    age: int | None = Field(default=None, ge=0, le=120)
    seniority: int | None = Field(default=None, ge=0, le=80)
    expertise: str | None = Field(default=None, max_length=200)
    short_intros: str | None = Field(default=None, max_length=200)
    teaching_city: str | None = Field(default=None, max_length=100)
    teaching_district: str | None = Field(default=None, max_length=100)
    target_learning: str | None = Field(default=None, max_length=255)
    teaching_method: str | None = Field(default=None, max_length=255)
    teaching_style: str | None = Field(default=None, max_length=100)

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
