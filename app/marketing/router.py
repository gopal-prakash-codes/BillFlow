from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, Response, RedirectResponse

from app.frontend.templates import template_response


router = APIRouter()


@router.get("/landing", response_class=HTMLResponse)
async def get_landing(request: Request):

    return template_response("./marketing/landing.html", request)


@router.get("/how-it-works", response_class=HTMLResponse)
async def how_it_works(request: Request):
    return template_response("./marketing/how-it-works.html", request)


@router.get("/about-us", response_class=HTMLResponse)
async def about_us(request: Request):
    return template_response("./marketing/about-us.html", request)

@router.get("/blog", response_class=HTMLResponse)
async def blog(request: Request):
    return template_response("./marketing/blog.html", request)

@router.get("/Terms-and-condititons", response_class=HTMLResponse)
async def terms(request: Request):
    return template_response("./marketing/terms.html", request)

@router.get("/data-privacy", response_class=HTMLResponse)
async def data_privacy(request: Request):
    return template_response("./marketing/data-privacy.html", request)

@router.get("/alternative-to-bill", response_class=HTMLResponse)
async def alternative_to_bill(request: Request):
    return template_response("./marketing/bill.html", request)


@router.get("/accounts-payable-debit-or-credit-journal-entries", response_class=HTMLResponse)
async def paid_form_page(request: Request):
    return template_response("./marketing/paid-form.html", request)


@router.get("/press-release", response_class=HTMLResponse)
async def press_release(request: Request):
    return template_response("./marketing/press-release.html", request)


@router.get("/general-ap-accounting", response_class=HTMLResponse)
async def general_ap_accounting(request: Request):
    return template_response("./marketing/general-ap-accounting.html", request)


@router.post("/paid-ap-invoice-general-entry/save")
async def store_paid_form_details(
    request: Request,
    name: str = Form(...),
    invoice_number: str = Form(...),
    invoice_date: str = Form(...),
    invoice_amount: str = Form(...),
    payment_date: str = Form(...),
    payment_amount: str = Form(...),
    payment_method: str = Form(...),
    expense_account: str = Form(...),
    payment_account: str = Form(...),
    memo: str = Form(...)):

    paid_form_details = request.session.get('paid_form_details')

    if not paid_form_details:
        paid_form_details = []

    data = {
        "vendor_name": name,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "invoice_amount": invoice_amount,
        "payment_date": payment_date,
        "payment_amount": payment_amount,
        "payment_method": payment_method,
        "expense_account": expense_account,
        "payment_account": payment_account,
        "memo": memo
    }

    paid_form_details.append(data)
    request.session['paid_form_details'] = paid_form_details
    return template_response("./marketing/paid-form.html", request)


@router.get("/manual-vs-automated-accounts-payable-whats-the-difference", response_class=HTMLResponse)
async def manual_account_payable_process(request: Request):
    return template_response("./marketing/manual-account-payable-process.html", request)

@router.get("/account-payable-glossary", response_class=HTMLResponse)
async def manual_account_payable_process(request: Request):
    return template_response("./marketing/account-payable-glossary.html", request)

@router.get("/sitemap")
async def sitemap(request: Request):
    with open('app/frontend/static/sitemap.xml', 'r') as f:
        data = f.read()
    return Response(content=data, media_type="application/xml")
