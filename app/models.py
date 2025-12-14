import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name:str
    password:str


class UserResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes=True


class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=300)


class CourseUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, min_length=1, max_length=300)


class CourseResponse(BaseModel):
    id: int
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=300)
    owner_id: int
    owner_name: str | None=Field(None)


    class Config:
        from_attributes=True


class MaterialCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    date_lesson: datetime.date

class MaterialUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    content: str | None = Field(None, min_length=1)
    date_lesson: datetime.date | None =Field(None)

class MaterialResponse(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    id: int
    course_id: int
    date_lesson: datetime.date
    counter: int = Field(default=1)

    class Config:
        from_attributes=True


class ProgressCreate(BaseModel):
    completed: bool = False

class ProgressResponse(BaseModel):
    id: int
    user_id: int
    material_id: int

    class Config:
        from_attributes=True