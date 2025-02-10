
from pydantic import BaseModel


class CaptchaSchema(BaseModel):
    captcha_text: str

    class Config:
        orm_mode = True