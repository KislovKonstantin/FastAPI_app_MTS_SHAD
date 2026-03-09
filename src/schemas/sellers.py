from pydantic import BaseModel, EmailStr, Field, ConfigDict
from .books import ReturnedBook

__all__ = [
    "PatchSeller",
    "IncomingSeller",
    "ReturnedSeller",
    "ReturnedAllSellers",
    "ReturnedSellerWithBooks",
]

class BaseSeller(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    email: EmailStr = Field(..., validation_alias="e_mail")

class PatchSeller(BaseModel):
    first_name: str | None = Field(None, max_length=50)
    last_name: str | None = Field(None, max_length=50)
    email: EmailStr | None = Field(None, validation_alias="e_mail")

class IncomingSeller(BaseSeller):
    password: str = Field(..., min_length=6)

class ReturnedSeller(BaseSeller):
    id: int
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class ReturnedAllSellers(BaseModel):
    sellers: list[ReturnedSeller]

class ReturnedSellerWithBooks(ReturnedSeller):
    books: list[ReturnedBook] = []