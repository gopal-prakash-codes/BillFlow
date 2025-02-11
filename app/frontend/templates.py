from typing import Optional

from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, Template
from app.db.session import SessionLocal
from app.db.models import Subscription
from app.payments.models import ProductTypeEnum

templates = Jinja2Templates(directory="app/frontend/templates")
email_templates = Environment(loader=FileSystemLoader("app/frontend/templates/email"))


# Helper util that will send session data automatically from request!
def template_response(
    template_name: str,
    request: Request,
    context: Optional[dict] = None,
    status_code: int = 200,
):
    if context is None:
        context = {}
    context["request"] = request
    context["session"] = request.session  # TODO: make sure that's secure to pass to FE
    with SessionLocal() as db:
        try:
            subscriptions = db.query(Subscription).filter(
                Subscription.user_id==request.session["user_id"],
                Subscription.product_type==ProductTypeEnum.approver_subscription
            ).first()

            context["is_subscribed"] = 1 if subscriptions else 0
        except Exception as e:
            context["is_subscribed"] = 0

    

    return templates.TemplateResponse(template_name, context, status_code=status_code)


def template_email(template_name: str, context: Optional[dict] = None) -> str:
    if context is None:
        context = {}
    t: Template = email_templates.get_template(template_name)
    return t.render(context)
