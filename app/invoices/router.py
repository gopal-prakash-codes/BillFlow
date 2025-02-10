import calendar
import io
from datetime import datetime
from typing import List, Optional

import fitz
import ulid
import jwt
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel
from result import Result
from starlette import status
from starlette.responses import StreamingResponse

from app.auth.utils import redirect_authentication, requires_authentication
from app.db.models import AgingReport, Subscription
from app.db.session import SessionLocal
from app.emails.utils import send_image_not_found_email
from app.frontend.templates import template_response
from app.invoices.aging_report.processor import AgingReportProcessor
from app.invoices.db_objects import AddPaymentDetailsPayload, ImageNotFoundEmailPayload
from app.invoices.ocr.textract import InvoiceImageProcessor, textract_client
from app.payments.models import PaymentPlanEnum, ProductTypeEnum
from app.vendors.db_utils import get_vendors_by_user
from app.users.db_utils import get_user_by_org_id
from app.approvers.utils import is_waiting_for_approval
from app.organizations.db_utils import get_organization_by_id


from ..utils import format_date_american
from .config import config
from .db_utils import (
    add_category_to_invoice,
    can_upload,
    can_upload_attachment,
    delete_invoice,
    get_aging_report_by_id,
    add_attachment_obj_to_db,
    get_invited_approvers,
    get_invoice_by_id,
    get_invoices_by_user,
    get_invoice_due_amount,
    get_invoices_by_organization,
    get_invoice_details,
    get_payment_details,
    invoice_upload_count,
    query_aging_reports,
    query_invoices,
    remove_category_from_invoice,
    save_invoice,
    save_payment_details,
    update_invoice_upload_count,
    update_paid_status_invoice,
    cancel_invoice_request,
    has_attachments
)
from .models import CreateInvoice, PublicAgingReport, PublicInvoice
from .s3_utils import (
    s3_client,
    upload_bytes_to_s3,
    upload_string_to_s3,
    upload_file,
    get_attachments_from_s3,
    create_zip_buffer
)
import rollbar

import csv
from io import StringIO

router = APIRouter()
processor = InvoiceImageProcessor(textract_client)


@router.get("/inbox", response_class=HTMLResponse)
async def get_home(
    request: Request,
    user_id: str = Depends(redirect_authentication),
    filter_by: str = None,
    order_by: str = "due_date",
    desc: bool = True,
    limit: int = 100,
    offset: int = 0,
):
    with SessionLocal() as db:
        invoices = get_invoices_by_user(
            db,
            user_id,
            filter_by=filter_by,
            order_by=order_by,
            limit=limit,
            offset=offset,
            desc=desc,
        )
        invoices = {invoice.id: PublicInvoice.from_orm(invoice).dict() for invoice in invoices.items}
    return template_response("./invoices/inbox.html", request, {"invoices": invoices})


@router.get("/invoice-list", response_class=HTMLResponse)
async def get_invoice_list(
    request: Request,
    user_id: str = Depends(redirect_authentication),
    filter_by: str = None,
    order_by: str = "due_date",
    desc: bool = True,
    limit: int = 5,
    total_pages: int = 1,
    current_page: int = 1,
):
    offset = (current_page - 1)* limit
    with SessionLocal() as db:
        paginated_invoices = get_invoices_by_user(
            db,
            user_id,
            filter_by=filter_by,
            order_by=order_by,
            limit=limit,
            offset=offset,
            desc=desc,
            total_pages=total_pages,
            current_page=current_page
        )
        next_page = None
        previous_page = None
        total_pages = paginated_invoices.total_pages
        if total_pages > 1:
            if current_page < total_pages:
                next_page_number = current_page + 1
                next_page = f"/invoice-list?current_page={next_page_number}"
            if current_page > 1:
                previous_page_number = current_page - 1
                if previous_page_number <= 0:
                    previous_page_number = 1
                previous_page = f"/invoice-list?current_page={previous_page_number}"
        invoices = {i.id: PublicInvoice.from_orm(i).dict() for i in paginated_invoices.items}
    return template_response(
        "./invoices/invoice-list.html",
        request,
        {
            "invoices": invoices,
            "current_page": current_page,
            "next_page": next_page,
            "previous_page": previous_page,
            "total_pages": total_pages
        }
    )


@router.get("/invoice-approvals-list", response_class=HTMLResponse)
async def get_invoice_list(
    request: Request,
    user_id: str = Depends(redirect_authentication),
    filter_by: Optional[str] = None,
    order_by: str = "due_date",
    desc: bool = True,
    limit: int = 100,
    offset: int = 0,
    total_pages: int = 1,
    current_page: int = 1,
):
    with SessionLocal() as db:
        invoices_data = []
        if not filter_by:
            invoices = get_invoices_by_user(
                    db,
                    user_id,
                    order_by=order_by,
                    limit=limit,
                    offset=offset,
                    desc=desc,
                    total_pages=total_pages,
                    current_page=current_page
                )
            for data in invoices.items:
                waiting_for_approval = is_waiting_for_approval(db, data.id)
                if not data.is_approved and waiting_for_approval:
                    invoices_data.append(PublicInvoice.from_orm(data, 0, waiting_for_approval[1]).dict())
                elif data.is_approved and waiting_for_approval:
                    invoices_data.append(PublicInvoice.from_orm(data, 1, waiting_for_approval[1]).dict())
        else:
            invoices = get_invoices_by_user(
                    db,
                    user_id,
                    filter_by=filter_by,
                    order_by=order_by,
                    limit=limit,
                    offset=offset,
                    desc=desc,
                    total_pages=total_pages,
                    current_page=current_page
                )
            if filter_by == "approved":
                for data in invoices.items:
                    waiting_for_approval = is_waiting_for_approval(db, data.id)
                    if data.is_approved and waiting_for_approval:
                        invoices_data.append(
                            PublicInvoice.from_orm(
                                data,
                                1,
                                waiting_for_approval[1]
                            ).dict())
            if filter_by == "wfa":
                for data in invoices.items:
                    waiting_for_approval = is_waiting_for_approval(db, data.id)
                    if not data.is_approved and waiting_for_approval:
                        invoices_data.append(
                            PublicInvoice.from_orm(
                                data,
                                0,
                                waiting_for_approval[1]
                            ).dict())
    return template_response(
        "./invoices/invoice-approvals-list.html", request, {"invoices": invoices_data}
    )


@router.get("/accountant/invoice-list", response_class=HTMLResponse)
async def get_invoice_list(
    request: Request,
    vendor: str = None,
    due_date: str = None,
    invoice_number: str = None,
    token: str = None,
    total_pages: int = 1,
    current_page: int = 1,
):
    if not token:
        return template_response(
            "./invoices/link-expired.html", request, context={"message": "Your link has been expired or corrupted"}
        )

    is_hidden = True
    if vendor or due_date or invoice_number:
        is_hidden = False

    data = jwt.decode(jwt=token, key='my-secret', algorithms='HS256')
    expiry_time = data['data']['exp']
    format = '%Y-%m-%d %H:%M:%S.%f'
    expiry_datetime = datetime.strptime(expiry_time, format)
    organization_id = data['data']['organization_id']

    if expiry_datetime < datetime.now():
        return Response(
            "Your link has been expired", status_code=status.HTTP_400_BAD_REQUEST
        )

    with SessionLocal() as db:
        paginated_invoices = get_invoices_by_organization(
            db,
            organization_id,
            vendor=vendor,
            due_date=due_date,
            invoice_number=invoice_number,
            total_pages=total_pages,
            current_page=current_page
        )
        next_page = None
        previous_page = None
        total_pages = paginated_invoices.total_pages
        if total_pages > 1:
            if current_page < total_pages:
                next_page_number = current_page + 1
                next_page = f"/invoice-list?current_page={next_page_number}"
            if current_page > 1:
                previous_page_number = current_page - 1
                if previous_page_number <= 0:
                    previous_page_number = 1
                previous_page = f"/invoice-list?current_page={previous_page_number}"
        invoices = {i.id: PublicInvoice.from_orm(i).dict() for i in paginated_invoices.items}
        user = get_user_by_org_id(db, organization_id)
        vendors = get_vendors_by_user(db, user.id)
    return template_response(
        "./invoices/invoice-list.html",
        request,
        {
            "invoices": invoices,
            "user_type": "accountant",
            "is_hidden": is_hidden,
            "vendors": vendors,
            "next_page": next_page,
            "previous_page": previous_page,
            "total_pages": total_pages,
            "current_page": current_page
        }
    )

@router.get("/accountant/view-invoice", response_class=RedirectResponse)
def view_invoice(
    request: Request,
    vendor: str = '',
    due_date: str = '',
    invoice_number: str = ''
):
    token = request._query_params.get('token')
    if not token:
        referer = request.__dict__.get('_headers').get('referer')
        token = (referer.split('token='))[-1]

    return RedirectResponse(
            f"/accountant/invoice-list?token={token}&vendor={vendor}&due_date={due_date}&invoice_number={invoice_number}",
            status_code=status.HTTP_302_FOUND,
        )


@router.get("/payment-detail/{invoice_id}", response_class=JSONResponse)
def get_invoice_payment_details(
    invoice_id: str,
    user_id: str = Depends(redirect_authentication)
):
    with SessionLocal() as db:
        payment_detail = get_payment_details(db, user_id, invoice_id)
        return JSONResponse(
            content={
                "invoice_number": payment_detail.invoice_number,
                "vendor_name": payment_detail.vendor,
                "account": payment_detail.account,
                "account_number": payment_detail.account_number,
                "amount": str(payment_detail.amount),
                "type": payment_detail.type,
                "paid_date": format_date_american(payment_detail.date)
            }
        )


@router.get("/paid-details", response_class=HTMLResponse)
async def get_paid_invoices(
    request: Request,
    user_id: str = Depends(redirect_authentication),
):
    with SessionLocal() as db:
        invoices = get_invoices_by_user(
            db,
            user_id,
            filter_by="paid"
        )
        invoices = {i.id: PublicInvoice.from_orm(i).dict() for i in invoices.items}
    return template_response(
        "./invoices/paid-details.html", request, {"invoices": invoices}
    )


@router.get("/invoices/{invoice_id}", response_class=HTMLResponse)
async def get_single_invoice(
    request: Request, invoice_id: str, user_id: str = Depends(redirect_authentication)
):
    with SessionLocal() as db:
        invoice = get_invoice_by_id(db, invoice_id)
        if not invoice:
            return Response(
                "404 Invoice not Found", status_code=status.HTTP_404_NOT_FOUND
            )
        invoice = PublicInvoice.from_orm(invoice)
        approvers = get_invited_approvers(db, user_id)
        waiting_for_approval = False if invoice.is_approved else is_waiting_for_approval(db, invoice_id)
        
        is_approver_sub_paid = False
        if db.query(Subscription).filter(Subscription.product_type == ProductTypeEnum.approver_subscription).first() is not None:
            is_approver_sub_paid = True

    return template_response(
        "./invoices/single-invoice.html",
        request,
        {
            "data": jsonable_encoder(invoice),
            "approvers": approvers,
            "is_approver_sub_paid": is_approver_sub_paid,
            "is_waiting_for_approval": waiting_for_approval
        },
    )


@router.get("/approve/invoice")
async def get_invoice(
    request: Request, token: str
):
    if not token:
        raise HTTPException(422, detail="Your link has been expired or corrupted")

    data = jwt.decode(jwt=token, key='my-secret', algorithms='HS256')
    expiry_time = data['data']['exp']
    format = '%Y-%m-%d %H:%M:%S.%f'
    expiry_datetime = datetime.strptime(expiry_time, format)

    if expiry_datetime < datetime.now():
        return template_response(
            "./invoices/link-expired.html", request, context={"message": "Your link has been expired"}
        )

    invoice_id = data['data']['invoice_id']

    with SessionLocal() as db:
        invoice = get_invoice_by_id(db, invoice_id)
        if not invoice:
            return Response(
                "404 Invoice not Found", status_code=status.HTTP_404_NOT_FOUND
            )
        invoice = PublicInvoice.from_orm(invoice)
    return template_response(
        "./invoices/single-invoice.html",
        request,
        {"data": jsonable_encoder(invoice), "user_type": "approver"},
    )


@router.get("/accountant/invoice/{invoice_id}")
async def get_invoice(
    request: Request, invoice_id: str
):
    referer = request.__dict__.get('_headers').get('referer')
    token = (referer.split('token='))[-1]
    token = token.split('&vendor')[0]

    if not token:
        raise HTTPException(422, detail="Your link has been expired or corrupted")

    data = jwt.decode(jwt=token, key='my-secret', algorithms='HS256')
    expiry_time = data['data']['exp']
    format = '%Y-%m-%d %H:%M:%S.%f'
    expiry_datetime = datetime.strptime(expiry_time, format)

    if expiry_datetime < datetime.now():
        return template_response(
            "./invoices/link-expired.html", request, context={"message": "Your link has been expired"}
        )

    with SessionLocal() as db:
        invoice = get_invoice_by_id(db, invoice_id)
        if not invoice:
            return Response(
                "404 Invoice not Found", status_code=status.HTTP_404_NOT_FOUND
            )
        invoice = PublicInvoice.from_orm(invoice)

    return template_response(
        "./invoices/single-invoice.html",
        request,
        {"data": jsonable_encoder(invoice), "user_type": "accountant", "token": token},
    )



@router.get("/invoice_images/{invoice_id}")
async def get_invoice_image(
    request: Request, invoice_id: str, user_id: str = Depends(requires_authentication)
):
    with SessionLocal() as db:
        invoice = get_invoice_by_id(db, invoice_id)
        if not invoice:
            return Response(status_code=status.HTTP_404_NOT_FOUND)
    f = io.BytesIO()
    s3_client.download_fileobj(config.s3_bucket_name, invoice.image_path, f)
    f.seek(0)
    return StreamingResponse(content=f, media_type=invoice.image_content_type)


@router.get("/invoice_image/{invoice_id}")
async def get_invoice_image(
    request: Request, invoice_id: str
):
    with SessionLocal() as db:
        invoice = get_invoice_by_id(db, invoice_id)
        if not invoice:
            return Response(status_code=status.HTTP_404_NOT_FOUND)
    f = io.BytesIO()
    s3_client.download_fileobj(config.s3_bucket_name, invoice.image_path, f)
    f.seek(0)
    return StreamingResponse(content=f, media_type=invoice.image_content_type)


@router.post("/invoices/{invoice_id}")
async def post_single_invoice(
    invoice_id: str, paid: bool, user_id: str = Depends(requires_authentication)
):
    with SessionLocal() as db:
        update_paid_status_invoice(db, invoice_id, is_paid=paid)
    return RedirectResponse(
        f"/invoices/{invoice_id}", status_code=status.HTTP_302_FOUND
    )


@router.get("/upload-invoice", response_class=HTMLResponse)
async def get_register(request: Request):
    return template_response("./invoices/upload.html", request)


@router.post("/upload-attachment/{invoice_id}", response_class=HTMLResponse)
async def post_upload_attachment(
    request: Request,
    invoice_id: str,
    attachment_type: str = Form(None),
    attachment: UploadFile = File(...),
    user_id: str = Depends(requires_authentication)
):
        if attachment_type is None or attachment is None:
            return RedirectResponse(
                    f"/invoices/{invoice_id}?error=Please select Type for Document to upload.", status_code=status.HTTP_302_FOUND
                )

        allow_list = ("jpg", "jpeg", "png", "pdf", "docx", "doc", "txt")
        file_extension = attachment.filename.split('.')[-1]
        print("JHGDBHJD: ", attachment.content_type)
        if file_extension not in allow_list:
            return RedirectResponse(
                    f"/invoices/{invoice_id}?error=File must be a .docx, .txt, .jpg, or .pdf", status_code=status.HTTP_302_FOUND
                )

        with SessionLocal() as db:
            # check if the user has a paid plan
            is_paid_plan, last_invoice_uploaded_month = can_upload_attachment(db=db, user_id=user_id)
            if is_paid_plan is None:
                return RedirectResponse(
                    f"/invoices/{invoice_id}?error=Please subscribe to our paid plan to avail this feature.", status_code=status.HTTP_302_FOUND
                )

        # try:
        file_data = await attachment.read()
        filename = attachment.filename
        file_obj = io.BytesIO(file_data)
        
        # Check if the file is corrupted
        if file_extension in ["jpg", "jpeg", "png"]:
            try:
                from PIL import Image

                with Image.open(file_obj) as img:
                    img.verify()
            except Exception:
                return RedirectResponse(
                    f"/invoices/{invoice_id}?error=Our system found your file corrupted, Please upload file in correct format.", status_code=status.HTTP_302_FOUND
                )
        elif file_extension in ['docx', 'doc']:
            try:
                import docx
                with docx.Document(file_obj) as doc:
                    pass
            except Exception:
                return RedirectResponse(
                    f"/invoices/{invoice_id}?error=Our system found your file corrupted, Please upload file in correct format.", status_code=status.HTTP_302_FOUND
                )
        elif file_extension == 'pdf':
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(file_obj)
                reader.pages
            except Exception as e:
                print(e)
                return RedirectResponse(
                    f"/invoices/{invoice_id}?error=Our system found your file corrupted, Please upload file in correct format.", status_code=status.HTTP_302_FOUND
                )
        elif file_extension == 'txt':
            try:
                file_data.decode("utf-8")
            except Exception as e:
                print(e)
                return RedirectResponse(
                    f"/invoices/{invoice_id}?error=Our system found your file corrupted, Please upload file in correct format.", status_code=status.HTTP_302_FOUND
                )

        # Raise error if size of file is larger than 1MB
        if len(file_data) > 1000000:
            return RedirectResponse(
                    f"/invoices/{invoice_id}?error=Document size should not be larger than 1MB.", status_code=status.HTTP_302_FOUND
                )

        object_name = f'{invoice_id}-{user_id}-{filename}'

        # Upload document to s3 bucket
        is_uploaded = upload_file(
            file_name=filename,
            file_data=file_data,
            bucket="apiattach",
            object_name=object_name,
            user_id=user_id,
            invoice_id=invoice_id,
            attachment_type=attachment_type
        )

        if is_uploaded:
            with SessionLocal() as db:
                add_attachment_obj_to_db(db, invoice_id, object_name, attachment_type)
            return RedirectResponse(
                    f"/invoices/{invoice_id}?message=Your document has been uploaded.", status_code=status.HTTP_302_FOUND
                )
        return RedirectResponse(
                    f"/invoices/{invoice_id}?error=Can't upload document.", status_code=status.HTTP_302_FOUND
                )



@router.post("/upload-invoice", response_class=HTMLResponse)
async def post_upload_invoice(
    request: Request, file: UploadFile = File(...), user_id: str = Depends(requires_authentication)
):
    allow_list = ("image/png", "image/jpeg", "image/jpg", "application/pdf")
    if file.content_type not in allow_list:
        raise HTTPException(422, detail="File must be a .png, .jpg, or .pdf")

    with SessionLocal() as db:
        is_paid_plan, last_invoice_uploaded_month = can_upload(db=db, user_id=user_id)
        if is_paid_plan is None or is_paid_plan.lower() == PaymentPlanEnum.free:
            current_month = datetime.now().month
            total_upload_count = invoice_upload_count(db=db, user_id=user_id)
            if total_upload_count >= 5 and current_month == last_invoice_uploaded_month:
                return template_response("./invoices/upload.html", request, context={"limit_reached": True})
            elif last_invoice_uploaded_month is None or current_month != last_invoice_uploaded_month:
                update_invoice_upload_count(db=db, user_id=user_id, current_month=current_month)

    file_data = await file.read()
    if file.content_type == "application/pdf":
        doc = fitz.open(stream=file_data, filetype="pdf")
        page = doc.load_page(0)  # number of page
        file_data = page.get_pixmap().tobytes(output="PNG")

    parse_result: Result = processor.apply(file_data)
    if not parse_result.is_ok:
        return parse_result.err()

    raw_parse = parse_result.ok()
    formatted_invoice = CreateInvoice.from_raw_parse(
        user_id, raw_parse, file.content_type
    )

    # Upload image to S3
    extension = file.content_type.split("/")[1]
    formatted_invoice.image_path = upload_bytes_to_s3(
        file_data, f"{str(ulid.ulid())}", extension
    )

    with SessionLocal() as db:
        # TODO: Use file data to upsert based on image md5 hash
        db_invoice = save_invoice(db, formatted_invoice)

    with SessionLocal() as db:
        update_invoice_upload_count(db=db, user_id=user_id)

    return RedirectResponse(
        f"/invoices/{db_invoice.id}", status_code=status.HTTP_302_FOUND
    )


class CalendarDay(BaseModel):
    year: int
    month: int
    day: int
    active: bool
    invoices_due: List[PublicInvoice] = []


@router.get("/calendar", response_class=HTMLResponse)
async def get_calendar(
    request: Request,
    year: int = None,
    month: int = None,
    next: bool = False,
    previous: bool = False,
    user_id: str = Depends(redirect_authentication),
):
    # Validate combindations
    if next and previous:
        raise HTTPException(400, "Can't specify previous and next.")

    # Build datetime from query params or default to now
    if not (month and year):
        month = datetime.utcnow().month
        year = datetime.utcnow().year
    current_dt = datetime(year, month, 1)

    # Make adjustments if indicated
    if next:
        current_dt = current_dt + relativedelta(months=1)
    if previous:
        current_dt = current_dt - relativedelta(months=1)

    # Ensure theser are up to date after any adjustments
    month, year = current_dt.month, current_dt.year

    with SessionLocal() as db:
        calendar_days = []
        calendar_view = calendar.Calendar(firstweekday=6)

        for date in calendar_view.itermonthdates(year, month):
            due_this_date = query_invoices(db, due_date=date, user_id=user_id)
            try:
                calendar_days.append(
                    CalendarDay(
                        year=date.year,
                        month=date.month,
                        day=date.day,
                        active=month == date.month,
                        invoices_due=[PublicInvoice.from_orm(i) for i in due_this_date.items],
                    )
                )
            except Exception as e:
                rollbar.report_exc_info(str(e))
                print(str(e))
                calendar_days.append(
                    CalendarDay(
                        year=date.year,
                        month=date.month,
                        day=date.day,
                        active=month == date.month,
                        invoices_due=[],
                    )
                )

    return template_response(
        "./invoices/calendar.html",
        request,
        {
            "date_string": current_dt.strftime("%B %Y"),
            "month": month,
            "year": year,
            "days": jsonable_encoder(calendar_days),
        },
    )


@router.get("/aging-reports/{report_id}", response_class=HTMLResponse)
async def get_aging_report(
    request: Request, report_id: str, user_id: str = Depends(redirect_authentication)
):
    with SessionLocal() as db:
        report = get_aging_report_by_id(db, report_id)
        report = PublicAgingReport.from_orm(report)
    return template_response(
        "./invoices/single-aging-report.html",
        request,
        {
            "report_html": report.csv_html(),
            "report": jsonable_encoder(report),
        },
    )


@router.get("/aging-reports/{report_id}/download")
async def download_aging_report(
    request: Request, report_id: str, user_id: str = Depends(redirect_authentication)
):
    with SessionLocal() as db:
        report = get_aging_report_by_id(db, report_id)
        if not report:
            return Response(status_code=status.HTTP_404_NOT_FOUND)
    f = io.BytesIO()
    s3_client.download_fileobj(config.s3_bucket_name, report.csv_uri, f)
    f.seek(0)
    return StreamingResponse(
        content=f,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="aging-report-{format_date_american(report.created_on)}.csv"'
        },
    )


@router.get("/paid-details/download")
async def download_paid_details(
    request: Request,
    user_id: str = Depends(redirect_authentication)
):
    with SessionLocal() as db:
        invoices = get_invoices_by_user(
            db,
            user_id,
            filter_by="paid"
        )

        csv_file = StringIO()
        csv_writer = csv.writer(csv_file)
        header = [
            "invoice_number",
            "vendor_name",
            "account",
            "account_number",
            "invoice_amount",
            "paid_amount",
            "type",
            "paid_date"
        ]
        csv_writer.writerow(header)
        records = []
        for invoice in invoices.items:
                payment_detail = get_payment_details(db, user_id, invoice.id)
                if payment_detail:
                    records.append([
                        payment_detail.invoice_number,
                        payment_detail.vendor,
                        payment_detail.account,
                        payment_detail.account_number,
                        get_invoice_due_amount(db, invoice.id),
                        str(payment_detail.amount),
                        payment_detail.type,
                        format_date_american(payment_detail.date)
                    ])

        if invoices:
            csv_writer.writerows(records)

        return StreamingResponse(
            content=iter(csv_file.getvalue()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="paid-details-{format_date_american(datetime.now())}.csv"'
            },
        )


@router.get("/invoice-list/download")
async def download_invoice_details(
    request: Request,
    user_id: str = Depends(redirect_authentication),
    filter_by: str = None
):
    with SessionLocal() as db:
        invoices = get_invoices_by_user(
            db,
            user_id,
            filter_by=filter_by
        )
        csv_file = StringIO()
        csv_writer = csv.writer(csv_file)
        header = [
            "vendor_name",
            "invoice_number",
            "due_amount",
            "status",
            "due_date",
            "category"
        ]
        csv_writer.writerow(header)
        records = []
        for invoice in invoices.items:
            invoice_details = get_invoice_details(db, invoice.id)
            if invoice_details:
                status = "Paid" if invoice_details.is_paid else "Overdue"
                formatted_due_date = format_date_american(invoice_details.due_date)
                invoice_id = invoice_details.invoice_id.replace('#', '')
                category_names = [association.category.name for association in invoice_details.category_links]
                records.append([
                    invoice_details.vendor_name,
                    invoice_id,
                    invoice_details.amount_due,
                    status,
                    formatted_due_date,
                    ", ".join(category_names)
                ])

        if invoices:
            csv_writer.writerows(records)

        return StreamingResponse(
            content=iter(csv_file.getvalue()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="invoice-details-{format_date_american(datetime.now())}.csv"'
            },
        )


@router.get("/aging-reports", response_class=HTMLResponse)
async def get_aging_reports(
    request: Request, user_id: str = Depends(redirect_authentication)
):
    with SessionLocal() as db:
        reports = query_aging_reports(db, user_id, order_by="created_on", desc=True)
        reports = [PublicAgingReport.from_orm(r) for r in reports]
    return template_response(
        "./invoices/aging-reports.html",
        request,
        {"reports": jsonable_encoder(reports)},
    )


@router.post("/aging-reports/create", response_class=RedirectResponse)
async def post_generate_aging_report(user_id: str = Depends(requires_authentication)):
    with SessionLocal() as db:
        data = AgingReportProcessor.fetch_data(db, user_id)
        df = AgingReportProcessor().apply(data)
        # Convert DF to buffer and save to S3
        stream = io.StringIO()
        stream.write(
            f'{datetime.utcnow().strftime("%m/%d/%Y")} - Accounts Payable Aging Report,\n,\n'
        )
        df.to_csv(stream, index=False)
        s3_uri = upload_string_to_s3(
            stream.getvalue(), f"aging-report-{datetime.utcnow()}-{ulid.ulid()}", "csv"
        )

        # Save report
        new_report = AgingReport(user_id=user_id, csv_uri=s3_uri)
        db.add(new_report)
        db.commit()

    return RedirectResponse("/aging-reports", status_code=status.HTTP_302_FOUND)


@router.post("/payment-details/create")
def add_payment_details(
    payload: AddPaymentDetailsPayload,
    user_id: str = Depends(requires_authentication)
):
    with SessionLocal() as db:
        save_payment_details(
            db=db,
            payment_type=payload.type,
            account=payload.account,
            account_number=payload.account_number,
            amount=payload.amount,
            vendor=payload.vendor,
            date=payload.date,
            user_id=user_id,
            invoice_id=payload.invoice_id
        )
    return Response(status_code=status.HTTP_201_CREATED)


@router.post("/not-found-email", response_class=JSONResponse)
def image_not_found_email(
    payload: ImageNotFoundEmailPayload,
    user_id: str = Depends(requires_authentication)
):
    """
        send email to freshdesk to open a trouble ticket
    """
    with SessionLocal() as db:
        invoice = get_invoice_by_id(db=db, invoice_id=payload.invoice_id)
        organization = get_organization_by_id(db, invoice.organization_id)

    send_image_not_found_email(
        invoice_id=payload.invoice_id,
        customer_id=invoice.user_id,
        aws_image_path=invoice.image_path,
        uploaded_on=invoice.created_on,
        company_name=organization.name
    )
    return Response(status_code=status.HTTP_200_OK)


# API routes - no redirects - pure actions


class AddCategoryBody(BaseModel):
    category_name: str


@router.put("/invoices/{invoice_id}/categories")
async def put_single_invoice(
    invoice_id: str,
    body: AddCategoryBody,
    user_id: str = Depends(requires_authentication),
):
    # Add categories
    with SessionLocal() as db:
        add_category_to_invoice(db, user_id, invoice_id, body.category_name)
    return Response(status_code=status.HTTP_201_CREATED)


@router.delete("/invoices/{invoice_id}/categories")
async def delete_invoice_category(
    invoice_id: str, category_name: str, user_id: str = Depends(requires_authentication)
):
    # Add categories
    with SessionLocal() as db:
        remove_category_from_invoice(db, user_id, invoice_id, category_name)
    return Response(status_code=status.HTTP_200_OK)


@router.delete("/invoices/{invoice_id}")
async def delete_single_invoice(
    invoice_id: str, user_id: str = Depends(requires_authentication)
):
    with SessionLocal() as db:
        delete_invoice(db, invoice_id)
    return Response(status_code=status.HTTP_200_OK)


@router.post("/approval/cancel/{invoice_id}")
async def cancel_single_invoice_request(
    invoice_id: str, user_id: str = Depends(requires_authentication)
):
    with SessionLocal() as db:
        cancel_invoice_request(db, invoice_id)
    return Response(status_code=status.HTTP_200_OK)


@router.get("/download-attachment")
async def get_attachments(
    request: Request, token: str
):
    invoice_token = request._query_params.get('token')
    payload_data = jwt.decode(invoice_token, "my-secret", algorithms=["HS256"])
    
    invoice_id  = payload_data['data']['invoice_id']
    with SessionLocal() as db:
        invoice = get_invoice_by_id(db, invoice_id)
        if not invoice:
            return Response(status_code=status.HTTP_404_NOT_FOUND)
        attachments = has_attachments(db, invoice_id)
        if not attachments:
            return JSONResponse(
                {"error":"No attachments found"}, 
                status_code=status.HTTP_302_FOUND
            )
    
    attachments_s3 = get_attachments_from_s3(invoice_id)
    if attachments_s3 is None:
         return JSONResponse(
                {"error":"No attachments found"}, 
                status_code=status.HTTP_302_FOUND
            )

    zip_buffer = create_zip_buffer(attachments_s3)
    headers = {
        'Content-Disposition': f'attachment; filename={invoice_id}_attachments.zip',
        'Content-Type': 'application/zip',
    }

    return StreamingResponse(iter([zip_buffer.read()]), headers=headers)
