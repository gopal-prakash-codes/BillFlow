from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND

from app.auth.utils import requires_authentication
from app.emails.utils import send_ap_staff_email
from app.frontend.templates import template_response

router = APIRouter()


@router.post("/invite-to-create-passwd", response_class=RedirectResponse)
def invite_to_create_passwd(
   request: Request,
   first_name: str = Form(...),
   last_name: str = Form(...),
   email: str = Form(...),
   user_id: str = Depends(requires_authentication),
):
    send_ap_staff_email(email=email)
    return RedirectResponse(
        f"/settings/account?message=Invitation Email has been sent to {email}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/create-password", response_class=HTMLResponse)
async def get_create_password(request: Request):
    return template_response("./manager/create-password.html", request)

@router.post("/create-password", response_class=HTMLResponse)
async def post_create_password(
    request: Request,   
    password: str = Form(...),
    confm_passwd: str = Form(...),
):
    return RedirectResponse("/login", status_code=HTTP_302_FOUND)
