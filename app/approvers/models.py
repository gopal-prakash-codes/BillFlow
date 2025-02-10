from pydantic import BaseModel


class ApprovalRejectionPayload(BaseModel):
    comment: str

    class Config:
        orm_mode = True
