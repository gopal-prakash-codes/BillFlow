from datetime import datetime, timedelta

import stripe
from fastapi import APIRouter, Depends, Form, Request
from fastapi.param_functions import Header
from fastapi.responses import HTMLResponse, RedirectResponse
from loguru import logger as log
from starlette.responses import JSONResponse
from starlette.status import HTTP_302_FOUND

from app.auth.utils import requires_authentication
from app.config import config as global_config
from app.db.session import SessionLocal
from app.frontend.templates import template_response
from app.payments.stripe_utils import update_customer_id, update_user_plan
from app.users.db_utils import get_user_by_id

from ..db.models import Organization, Plan, Subscription
from .config import config
from .db_utils import update_user_payment_plan
from .models import PriceID, ProductTypeEnum, RequestPlan

router = APIRouter()
stripe.api_key = config.stripe_secret_key


@router.get("/select-plan", response_class=HTMLResponse)
async def get_select_plan(
    request: Request, user_id: int = Depends(requires_authentication)
):
    with SessionLocal() as db:
        plans = db.query(
                Plan
            ).filter(
                Plan.product_type==ProductTypeEnum.user_subscription).all()
        user = get_user_by_id(db, user_id)

    return template_response(
        "./payments/select-plan.html",
        request,
        context={
            "plans": plans,
            "current_plan": user.paid_plan,
            "product_type": ProductTypeEnum.user_subscription,
            "publishable_key": config.stripe_publishable_key
        }
    )

@router.get("/subscriptions/success", response_class=HTMLResponse)
async def get_subscriptions_success(
    request: Request,
    plan: str,
    session_id: str,
    user_id: str = Depends(requires_authentication),
):
    with SessionLocal() as db:
        update_user_payment_plan(db, user_id, plan, session_id)
    return template_response("./payments/success.html", request)


@router.get("/subscriptions/cancel", response_class=HTMLResponse)
async def get_subscriptions_cancel(
    request: Request, user_id: str = Depends(requires_authentication)
):
    return template_response("./payments/cancelled.html", request)


@router.post("/create-checkout-session", response_class=RedirectResponse)
async def get_checkout(
    plan_key: str = Form(...), user_id: int = Depends(requires_authentication)
):
    if plan_key == "free":
        return RedirectResponse("/home", status_code=HTTP_302_FOUND)
    try:
        prices = stripe.Price.list()

        log.debug(f"PRICEs, {prices}, KEY {plan_key}")

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": prices.data[0].id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=global_config.base_domain
            + f"/subscriptions/success?plan={plan_key}"
            + "&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=global_config.base_domain + "/subscriptions/cancel",
        )

        # TODO save session_id to user table?

        return RedirectResponse(checkout_session.url, status_code=303)
    except Exception as e:
        log.exception(e)
        return JSONResponse({"error": "An unknown error occured"}, status_code=500)


@router.post("/create-portal-session", response_class=RedirectResponse)
async def customer_portal(user_id: str = Depends(requires_authentication)):
    # For demonstration purposes, we're using the Checkout session to retrieve the customer ID.
    # Typically this is stored alongside the authenticated user in your database.
    with SessionLocal() as db:
        user = get_user_by_id(db, user_id)

    checkout_session = stripe.checkout.Session.retrieve(user.stripe_session_id)

    portalSession = stripe.billing_portal.Session.create(
        customer=checkout_session.customer,
        return_url=global_config.base_domain,  # Redirect back to home/dashboard
    )
    return RedirectResponse(portalSession.url, status_code=303)


@router.post("/stripe-webhook", response_class=JSONResponse)
async def webhook_received(
    request: Request, signature: str = Header(None, alias="stripe-signature")
):
    # Replace this endpoint secret with your endpoint's unique secret
    # If you are testing with the CLI, find the secret by running 'stripe listen'
    # If you are using an endpoint defined with the API or dashboard, look in your webhook settings
    # at https://dashboard.stripe.com/webhooks
    request_json = await request.json()

    if config.stripe_webhook_secret:
        try:
            event = stripe.Webhook.construct_event(
                payload=request_json,
                sig_header=signature,
                secret=config.stripe_webhook_secret,
            )
        except Exception as e:
            return e
        # Get the type of webhook event sent - used to check the status of PaymentIntents.
        event_type = event["type"]
    else:
        event_type = request_json["type"]

    log.debug(f"stripe event:  {event_type}")

    if event_type == "checkout.session.completed":
        print("🔔 Payment succeeded!")

    elif event_type == "customer.subscription.trial_will_end":
        print("Subscription trial will end")

    elif event_type == "customer.subscription.created":
        print("Subscription created %s", event.id)

    elif event_type == "customer.subscription.updated":
        print("Subscription updated %s", event.id)

    elif event_type == "customer.subscription.deleted":
        # handle subscription cancelled automatically based
        # upon your subscription settings. Or if the user cancels it.
        print("Subscription canceled: %s", event.id)

    return JSONResponse({"status": "success"})


@router.post("/create-payment-intent", response_class=JSONResponse)
async def stripeIntent(
    intent_data: RequestPlan,
    request: Request,
    user_id: str = Depends(requires_authentication),
):
    price_id = intent_data.price_id
    payment_method = intent_data.payment_method


    try:
        with SessionLocal() as db:
            user = get_user_by_id(db, user_id)
        if user:
            price = db.query(Plan).filter(Plan.stripe_plan_id==price_id).first()
            if price.plan_key == "Free":
                raise stripe.error.InvalidRequestError
            if not user.customer_id:
                customer = stripe.Customer.create(
                    name=user.name,
                    email=user.email,
                    invoice_settings={
                        "default_payment_method": payment_method,
                    },
                )

                update_customer_id(db=db, user_id=user.id, customer_id=customer["id"])
            else:
                stripe.PaymentMethod.attach(
                    str(payment_method), customer=user.customer_id
                )

                stripe.Customer.modify(
                    user.customer_id,
                    invoice_settings={
                        "default_payment_method": payment_method,
                    },
                )

            user_subscription = db.query(Subscription).filter(Subscription.user_id==user_id, Subscription.product_type==price.product_type).first()
            if user_subscription:
                subscription = stripe.Subscription.modify(
                    user_subscription.subscription_id,
                    proration_behavior=None,
                    payment_settings={'save_default_payment_method': 'on_subscription'},
                    expand=['latest_invoice.payment_intent'],
                )
                now = datetime.now()
                user_subscription.subscription_id = subscription.id
                user_subscription.plan_id = price.id
                user_subscription.subscribed_at = now
                user_subscription.expires_at = now + timedelta(days=30)
                user_subscription.product_type = price.product_type
                db.commit()
                db.refresh(user_subscription)
            else:
                subscription = stripe.Subscription.create(
                    customer=user.customer_id,
                    items=[
                        {"price": price_id},
                    ],
                    payment_settings={'save_default_payment_method': 'on_subscription'},
                    expand=['latest_invoice.payment_intent'],
                )
                
                now = datetime.now()

                sub = Subscription(
                    subscription_id=subscription.id,
                    user_id=user_id,
                    plan_id=price.id,
                    subscribed_at=now,
                    expires_at=(now + timedelta(days=30)),
                    product_type=price.product_type
                )
                db.add(sub)
                db.commit()
                db.refresh(sub)

            payment_intent = subscription.latest_invoice.payment_intent
            return JSONResponse(
                {
                    "error_status": None,
                    "error_code": None,
                    "client_secret": payment_intent.client_secret,
                    "payment_status": payment_intent.status,
                    "intent_id": payment_intent.id,
                    "customer": user.customer_id,
                    "price_id": price.stripe_plan_id
                }
            )
        else:
            return JSONResponse({"error_code": "unauthorized", "error_status": 401})

    except stripe.error.CardError as error:
        return JSONResponse(
            content={
                "error_status": error.http_status,
                "error_code": error.code,
                "client_secret": None,
            }
        )
    except stripe.error.InvalidRequestError as error:
        return JSONResponse(
            content={
                "error_status": error.http_status,
                "error_code": error.code,
                "client_secret": None,
            }
        )
    except Exception as e:
        log.error(str(e))
        return JSONResponse(
            content={"error_status": 400, "error_code": "error", "client_secret": None}
        )


@router.post("/upgrade-plan", response_class=JSONResponse)
async def upgradePlan(
    price: PriceID,
    request: Request,
    user_id: str = Depends(requires_authentication),
):
    with SessionLocal() as db:
        user = get_user_by_id(db, user_id)
    if user:
        company = (
            db.query(Organization)
            .filter(Organization.id == user.organization_id)
            .first()
        )

        plan = db.query(Plan).filter(Plan.stripe_plan_id==price.price_id).first()

        if plan:
            paid_plan = plan.plan_key
            plan_expiry = datetime.now() + timedelta(days=30)
            plan_started = datetime.now()
            plan_id = plan.stripe_plan_id
        
        if plan.product_type == ProductTypeEnum.user_subscription:
            update_user_plan(db, user_id, paid_plan, plan_expiry, plan_started, plan_id)

        data = {
            "email": user.email,
            "product": "Premium",
            "quantity": "Monthly",
            "company_name": company.name,
            "total_price": int(plan.plan_price),
        }
        return JSONResponse(data)
