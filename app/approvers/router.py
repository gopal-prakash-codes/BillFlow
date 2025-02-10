from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from starlette import status
from starlette.responses import JSONResponse, Response
from app.approvers.models import ApprovalRejectionPayload
from app.emails.utils import send_approver_request_email, send_invitation_email
from app.payments.models import ProductTypeEnum, TierEnum

from currency_symbols import CurrencySymbols

import jwt

from app.users.models import User
from app.db.session import SessionLocal
from app.auth.utils import requires_authentication
import app.db.models as db_models
import app.invoices.db_utils as invoice_utils

from .utils import add_requested_approver


router = APIRouter()


@router.post("/approver/invite", response_class=User)
def invite_approver(
   request: Request,
   first_name: str = Form(...),
   last_name: str = Form(...),
   email: str = Form(...),
   user_id: str = Depends(requires_authentication)
):
    with SessionLocal() as db:
      user_subscription = db.query(db_models.Subscription).filter_by(user_id=user_id, product_type=ProductTypeEnum.approver_subscription).first()
      plan = db.query(db_models.Plan).filter_by(id=user_subscription.plan_id).first()
      invited_approvers = db.query(db_models.InvitedApprover).filter_by(invited_by=user_id)

      if invited_approvers.count() >= plan.max_approvers:
        return RedirectResponse(
            f"/settings/account?message=Max {plan.max_approvers_raw} Approver can be invited.",
            status_code=status.HTTP_302_FOUND,
        )

      existing_user = invited_approvers.filter_by(email=email).first()
      if existing_user:
        return RedirectResponse(
            f"/settings/account?message={email} has been already invited",
            status_code=status.HTTP_302_FOUND,
        )
      new_approver = db_models.InvitedApprover(
       first_name=first_name,
       last_name=last_name,
       email=email,
       invited_by=user_id
      )
      db.add(new_approver)
      db.commit()
      db.refresh(new_approver)
    send_invitation_email(email=email)
    return RedirectResponse(
        f"/settings/account?message=Invitation Email has been sent to {email}",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/approval/reject/{invoice_id}")
def reject_invoice_approval(
    request: Request,
    invoice_id: str,
    comment: str = Form(...)
):
    referer = request.__dict__.get('_headers').get('referer')
    token = (referer.split('token='))[-1]
    with SessionLocal() as db:
        invoice = db.query(db_models.Invoice).filter_by(id=invoice_id).first()
        invoice.is_rejected = True
        invoice.rejection_reason = comment
        db.commit()
        db.refresh(invoice)
    return RedirectResponse(
        f"/approve/invoice?token={token}",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/approval/approve/{invoice_id}")
def reject_invoice_approval(
    request: Request,
    invoice_id: str,
):
    referer = request.__dict__.get('_headers').get('referer')
    token = (referer.split('token='))[-1]
    with SessionLocal() as db:
        invoice = db.query(db_models.Invoice).filter_by(id=invoice_id).first()
        invoice.is_approved = True
        db.commit()
        db.refresh(invoice)
    return RedirectResponse(
        f"/approve/invoice?token={token}",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/assign-tier")
def assign_tier(
    request: Request,
    selected_tier: str = Form(...),
    approver_id: str = Form(...),
    user_id: str = Depends(requires_authentication)
):
    with SessionLocal() as db:
        approver = db.query(db_models.InvitedApprover).filter_by(id=approver_id, invited_by=user_id).first()
        approver.approval_tier = selected_tier
        db.commit()
        db.refresh(approver)
    return JSONResponse(
        {"status": 201},
    )


@router.post("/approver/request/{invoice_id}")
async def send_approver_request(
    request: Request,
    invoice_id: str,
    user_id: str = Depends(requires_authentication),
    approver_id: str = Form(...),
):
    expires_on = datetime.now() + timedelta(hours=30)
    payload_data = {
        "approver_id": approver_id,
        "invoice_id": invoice_id,
        "exp": str(expires_on)
    }

    with SessionLocal() as db:
        invoice = invoice_utils.get_invoice_by_id(db, invoice_id)
        amount_due = invoice.raw_amount_due
        if invoice.currency and invoice.currency == '$':
            currency_symbol = '$'
        elif invoice.currency:
            currency_symbol = CurrencySymbols.get_symbol(invoice.currency)
            amount_due = f"{currency_symbol} {invoice.amount_due}"
        
        if not invoice:
            return Response(
                "404 Invoice not Found", status_code=status.HTTP_404_NOT_FOUND
            )

        approver = db.query(db_models.InvitedApprover).filter_by(id=approver_id).first()
        
        approval_tier = db.query(db_models.ApproverTierSetting)\
                        .filter_by(
                            user_id=user_id,
                            approval_tier=approver.approval_tier
                        )\
                        .first()

        if not approval_tier:
            return RedirectResponse(
            f"/invoices/{invoice_id}?message=Please assign an approval tier permission first before sending request to {approver.first_name} {approver.last_name}.",
            status_code=status.HTTP_302_FOUND,
        )

        category_query = db.query(db_models.CategoryInvoiceAssociation)\
        .outerjoin(db_models.Invoice)\
        .where(db_models.CategoryInvoiceAssociation.invoice_id==invoice.id)\
        .first()

        # uncomment if need to validate with category also
        # if not category_query:
        #     return RedirectResponse(
        #         f"/invoices/{invoice_id}?message=Please review approvers permissions as they do not match this invoice",
        #         status_code=status.HTTP_302_FOUND,
        #     )

        # category = db.query(db_models.Category).filter_by(id=category_query.category_id).first()

        if (
                not (invoice.amount_due >= approval_tier.amount_from and
                invoice.amount_due <= approval_tier.amount_to) 
                # uncomment if need to validate with category also
                # or not (category.name == approval_tier.category)
        ):
            return RedirectResponse(
                f"/invoices/{invoice_id}?message=Please review approvers permissions as they do not match this invoice",
                status_code=status.HTTP_302_FOUND,
            )

    with SessionLocal() as db:
        approver = db.query(db_models.InvitedApprover).filter_by(id=approver_id).first()
        token = jwt.encode({"data": payload_data}, "my-secret", algorithm="HS256")
        send_approver_request_email(
            email=approver.email,
            username=f"{approver.first_name} {approver.last_name}",
            invoice_number=invoice.invoice_id,
            token=token,
            amount_due=amount_due
        )
        add_requested_approver(db, user_id=user_id, approver_id=approver_id, invoice_id=invoice_id, expires_on=expires_on)
        return RedirectResponse(
            f"/invoices/{invoice_id}?message=Invitation for invoice approval sent to {approver.email}",
            status_code=status.HTTP_302_FOUND,
        )


@router.post("/approver/tier/add")
async def send_approver_request(
    request: Request,
    user_id: str = Depends(requires_authentication),
    amount_from_tier1: str = Form(...),
    amount_to_tier1: str = Form(...),
    category_tier1: str = Form(...),
    role_tier1: str = Form(''),
    amount_from_tier2: str = Form(None),
    amount_to_tier2: str = Form(None),
    category_tier2: str = Form(None),
    role_tier2: str = Form(''),
    amount_from_tier3: str = Form(None),
    amount_to_tier3: str = Form(None),
    category_tier3: str = Form(None),
    role_tier3: str = Form('')
):
    with SessionLocal() as db:
        approver_tiers = db.query(db_models.ApproverTierSetting).filter(db_models.ApproverTierSetting.user_id==user_id).all()
        if not approver_tiers:
            tier_1 = db_models.ApproverTierSetting(
                approval_tier=TierEnum.tier_1,
                user_id=user_id,
                amount_from=amount_from_tier1,
                amount_to=amount_to_tier1,
                category=category_tier1,
                role=role_tier1
            )

            db.add(tier_1)
            db.commit()
            db.refresh(tier_1)

            tier_2 = db_models.ApproverTierSetting(
                approval_tier=TierEnum.tier_2,
                user_id=user_id,
                amount_from=amount_from_tier2,
                amount_to=amount_to_tier2,
                category=category_tier2,
                role=role_tier2
            )

            db.add(tier_2)
            db.commit()
            db.refresh(tier_2)

            tier_3 = db_models.ApproverTierSetting(
                approval_tier=TierEnum.tier_3,
                user_id=user_id,
                amount_from=amount_from_tier3,
                amount_to=amount_to_tier3,
                category=category_tier3,
                role=role_tier3
            )

            db.add(tier_3)
            db.commit()
            db.refresh(tier_3)
        else:
            tier_1 = db.query(db_models.ApproverTierSetting).filter(db_models.ApproverTierSetting.approval_tier==TierEnum.tier_1).first()
            if tier_1:
                tier_1.amount_from = amount_from_tier1
                tier_1.amount_to = amount_to_tier1
                tier_1.category = category_tier1
                tier_1.role = role_tier1
                db.commit()
                db.refresh(tier_1)

            tier_2 = db.query(db_models.ApproverTierSetting).filter(db_models.ApproverTierSetting.approval_tier==TierEnum.tier_2).first()
            if tier_2:
                tier_2.amount_from = amount_from_tier2
                tier_2.amount_to = amount_to_tier2
                tier_2.category = category_tier2
                tier_2.role = role_tier2
                db.commit()
                db.refresh(tier_2)

            tier_3 = db.query(db_models.ApproverTierSetting).filter(db_models.ApproverTierSetting.approval_tier==TierEnum.tier_3).first()
            if tier_3:
                tier_3.amount_from = amount_from_tier3
                tier_3.amount_to = amount_to_tier3
                tier_3.category = category_tier3
                tier_3.role = role_tier3
                db.commit()
                db.refresh(tier_3)
        
    return RedirectResponse(
        f"/settings/account?message=Tier permissions are configured",
        status_code=status.HTTP_302_FOUND,
    )
