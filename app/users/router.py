from fastapi import APIRouter, Depends, Form, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, constr
from starlette.responses import JSONResponse
from starlette import status

import app.invoices.db_utils as invoice_utils
from urllib.parse import urlencode
from starlette.status import HTTP_302_FOUND
import jwt
from datetime import datetime, timedelta
from app.auth.utils import redirect_authentication, requires_authentication
from app.db.models import ApproverTierSetting, Organization, Plan, Subscription
from app.db.models import User as UserModel
from app.db.session import SessionLocal
from app.frontend.templates import template_response
from app.payments.models import ProductTypeEnum, TierEnum
from app.users.db_utils import get_user_by_id
from app.vendors.db_utils import update_leads_by_organization_id
from app.users.utils import get_approvers_list, add_visitor
from app.emails.utils import send_accountant_invitation_email
from app.payments.config import config

from .models import Approver, User

router = APIRouter()


class DashboardData(BaseModel):
    num_due_soon: int
    num_overdue: int
    num_paid: int


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(
    request: Request, user_id: str = Depends(redirect_authentication)
):
    with SessionLocal() as db:
        num_due_soon = invoice_utils.get_num_due_soon(db, user_id)
        num_overdue = invoice_utils.get_num_overdue(db, user_id)
        num_paid = invoice_utils.get_num_paid(db, user_id)

    data = DashboardData(
        num_due_soon=num_due_soon, num_overdue=num_overdue, num_paid=num_paid
    )

    return template_response(
        "./users/dashboard.html", request, {"data": jsonable_encoder(data)}
    )


@router.get("/settings/account", response_class=HTMLResponse)
async def get_settings_account(
    request: Request, user_id: str = Depends(redirect_authentication)
):
    with SessionLocal() as db:
        plans = db.query(Plan).filter(Plan.product_type=='approver_subscription').all()
        user = get_user_by_id(db, user_id)
        user = User.from_orm(user)
        subscriptions = db.query(Subscription).filter(Subscription.user_id==user_id).join(Plan).filter(Subscription.plan_id==Plan.id).add_columns(Plan.plan_key, Plan.max_approvers_raw)
        user_subscription = subscriptions.filter(Subscription.product_type==ProductTypeEnum.user_subscription).first()
        approver_subscription = subscriptions.filter(Subscription.product_type==ProductTypeEnum.approver_subscription).first()
        tier_settings = db.query(ApproverTierSetting).filter(ApproverTierSetting.user_id==user_id)
        tier_setting_1 = tier_settings.filter(ApproverTierSetting.approval_tier==TierEnum.tier_1).first()
        tier_setting_2 = tier_settings.filter(ApproverTierSetting.approval_tier==TierEnum.tier_2).first()
        tier_setting_3 = tier_settings.filter(ApproverTierSetting.approval_tier==TierEnum.tier_3).first()
        
        approvers = get_approvers_list(user_id=user_id)
        approvers = [Approver.from_orm(approver) for approver in approvers.all()]
    return template_response(
        "./users/account-settings.html",
        request,
        {
            "user": jsonable_encoder(user),
            "plans": plans,
            "product_type": "approver_subscription",
            "user_subscription": user_subscription[1] if user_subscription else user_subscription,
            "approver_subscription": approver_subscription[1] if approver_subscription else approver_subscription,
            "max_approvers_raw": approver_subscription[2] if approver_subscription else approver_subscription,
            "tier_setting_1": tier_setting_1,
            "tier_setting_2": tier_setting_2,
            "tier_setting_3": tier_setting_3,
            "approvers": approvers,
            "publishable_key": config.stripe_publishable_key
        },
    )


class SettingsUpdateCompany(BaseModel):
    company_name: constr(max_length=40, strip_whitespace=True, strict=True)


@router.patch("/settings/company_name", response_class=JSONResponse)
async def change_company_name(
    request: Request,
    body: SettingsUpdateCompany,
    user_id: str = Depends(requires_authentication),
):
    with SessionLocal() as db:
        organization: Organization = (
            db.query(Organization).join(UserModel).filter(UserModel.id == user_id).one()
        )
        organization.name = body.company_name
        db.commit()
    return JSONResponse({"status": "success"})


class SettingsUpdateFullName(BaseModel):
    full_name: constr(max_length=100, strip_whitespace=True, strict=True)


@router.patch("/settings/full_name", response_class=JSONResponse)
async def change_full_name(
    request: Request,
    body: SettingsUpdateFullName,
    user_id: str = Depends(requires_authentication),
):
    with SessionLocal() as db:
        user: UserModel = get_user_by_id(db, user_id)
        user.name = body.full_name
        db.commit()
    return JSONResponse({"status": "success"})


@router.post("/invite-accountant", response_class=RedirectResponse)
def invite_approver(
   request: Request,
   accountant_name: str = Form(...),
   accountant_email: str = Form(...),
   user_id: str = Depends(requires_authentication),
):

    with SessionLocal() as db:
        user: UserModel = get_user_by_id(db, user_id)
        payload_data = {
            "organization_id": user.organization_id,
            "accountant_email": accountant_email,
            "exp": str(datetime.now() + timedelta(hours=36))
        }
        token = jwt.encode({"data": payload_data}, "my-secret", algorithm="HS256")
        organization = db.query(Organization).filter_by(id=user.organization_id).first()
        send_accountant_invitation_email(company_name=organization.name, accountant_email=accountant_email, username=accountant_name, token=token)
        update_leads_by_organization_id(db, email=accountant_email, organization_id=user.organization_id)
    return RedirectResponse(
            f"/settings/account?message=Invitation sent to {accountant_email}.",
            status_code=status.HTTP_302_FOUND,
        )


@router.post("/visitor/add")
async def update_vendor(
    request: Request,
    email: str = Form(...),
    lead_captcha: str = Form(...),
):
    if lead_captcha.lower() != request.session.get('captcha'):   
        params = urlencode({"lead_captcha_error": "Invalid captcha, Please try again!"})
        return RedirectResponse(f"/landing?{params}", status_code=HTTP_302_FOUND)
    with SessionLocal() as db:
        add_visitor(db, email)
    return RedirectResponse(
            f"/landing?message=Thanks for subscribing!",
            status_code=status.HTTP_302_FOUND,
        )
