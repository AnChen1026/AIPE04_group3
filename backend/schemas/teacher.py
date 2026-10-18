from pydantic import BaseModel

class TeacherIn(BaseModel):
    name: str
    gender: str
    age: int
    seniority: int
    expertise: str
    short_intros: str
    teaching_city: str
    teaching_district: str
    target_learning: str
    teaching_method: str
    teaching_style: str

    status: str = "active"

