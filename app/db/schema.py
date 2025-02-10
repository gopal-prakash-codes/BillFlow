from pydantic import BaseModel


class PaginateResponse(BaseModel):
    limit: int = 0
    offset: int = 0
    total_pages: int = 1
    current_page: int = 1