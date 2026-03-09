from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_core import PydanticCustomError

__all__ = [
    "PatchBook",
    "IncomingBook",
    "ReturnedBook",
    "ReturnedAllBooks",
]


class BaseBook(BaseModel):
    title: str
    author: str
    year: int
    pages: int = Field(default=100, validation_alias="count_pages")

class PatchBook(BaseModel):
    title: str | None = None
    author: str | None = None
    year: int | None = None
    pages: int = Field(default=100, validation_alias="count_pages")
    seller_id: int | None = None

class IncomingBook(BaseBook):
    pages: int = Field(default=100, validation_alias="count_pages")
    seller_id: int
    model_config = ConfigDict(populate_by_name=True)

    @field_validator("year")
    @staticmethod
    def validate_year(val: int):
        if val < 1500:
            raise PydanticCustomError("Validation error", "Year is too old!")
        return val


class ReturnedBook(BaseBook):
    title: str
    author: str
    year: int
    id: int
    pages: int
    seller_id: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class ReturnedAllBooks(BaseModel):
    books: list[ReturnedBook]