from pydantic import BaseModel


class CodeIn(BaseModel):
    code: str


class Codes(BaseModel):
    codes: list[str]
