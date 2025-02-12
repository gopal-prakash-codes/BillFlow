from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.admin.models import AdminUserView, AdminLeadsView
from app.auth.utils import admin_authentication
from app.db.models import User, Lead
from app.db.session import SessionLocal
from app.frontend.templates import template_response
from fastapi.responses import StreamingResponse
import io
import pandas as pd


router = APIRouter(
    dependencies=[Depends(admin_authentication)],
)


@router.get("/admin/home", response_class=HTMLResponse)
async def get_admin_home(request: Request):
    with SessionLocal() as db:
        users = db.query(User).order_by(User.created_on.desc()).all()
        users = [AdminUserView.load_from_db(u) for u in users]

        leads = db.query(Lead).order_by(Lead.create_date.desc()).all()
        leads = [AdminLeadsView.load_from_db(lead) for lead in leads]
    return template_response("./admin/admin-home.html", request, {"users": users, "leads": leads})


@router.get("/download_csv")
async def get_csv(request: Request, type: str):

    with SessionLocal() as db:
        data = []
        if type == "user":
            users = db.query(User).order_by(User.created_on.desc()).all()
            data = [AdminUserView.load_from_db(u).dict() for u in users]
        else:
            leads = db.query(Lead).order_by(Lead.create_date.desc()).all()
            data = [AdminLeadsView.load_from_db(lead).dict() for lead in leads]

        df = pd.DataFrame(
            data=data
        )

        stream = io.StringIO()
        df.to_csv(stream, index = False)

        response = StreamingResponse(iter([stream.getvalue()]),
                            media_type="text/csv"
        )

        response.headers["Content-Disposition"] = "attachment; filename=export.csv"
    return response