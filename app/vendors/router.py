from fastapi import APIRouter, Depends, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from io import StringIO
import csv
from datetime import datetime

from app.auth.utils import redirect_authentication, requires_authentication
from app.db.session import SessionLocal
from app.frontend.templates import template_response
from app.invoices.db_utils import query_invoices
from app.invoices.models import PublicInvoice
from app.users.db_utils import get_user_by_id
from app.utils import format_date_american

from .db_utils import (
    get_vendor_by_id, 
    get_vendors_by_user, 
    update_vendor_contact_email, add_leads_data, 
    update_vendor_info
)
from .models import PublicVendorView

router = APIRouter()


@router.get("/vendors", response_class=HTMLResponse)
async def get_vendors(
    request: Request, user_id: str = Depends(redirect_authentication)
):
    with SessionLocal() as db:
        vendors = get_vendors_by_user(db, user_id)
        vendors = [PublicVendorView.load(db, v) for v in vendors]
    return template_response(
        "./vendors/vendors.html",
        request,
        {"vendors": jsonable_encoder(vendors)},
    )


@router.get("/vendors/{vendor_id}", response_class=HTMLResponse)
async def get_single_vendor(
    request: Request, vendor_id: str, user_id: str = Depends(redirect_authentication)
):
    with SessionLocal() as db:
        vendor = get_vendor_by_id(db, vendor_id)
        if not vendor:
            return Response("404 Vendor not found.", status_code=404)
        vendor = PublicVendorView.load(db, vendor)
        invoices = [
            PublicInvoice.from_orm(i)
            for i in query_invoices(
                db, vendor_id=vendor_id, order_by="created_on", desc=True
            ).items
        ]

    return template_response(
        "./vendors/single-vendor.html",
        request,
        {
            "vendor": jsonable_encoder(vendor),
            "invoices": jsonable_encoder(invoices),
        },
    )


# API ROUTES


class VendorUpdateBody(BaseModel):
    contact_email: str


class VendorEditBody(BaseModel):
    vendor_name: str
    vendor_number: int
    external_vendor_id: int
    address_one: str
    address_two: str
    city: str
    state: str
    pincode: int
    attention: str
    phone: str
    fax: str
    parent_vendor: int
    account: str
    tax_id: str
    note: str


@router.put("/vendors/{vendor_id}")
async def update_vendor(
    vendor_id: str,
    body: VendorUpdateBody,
    user_id: str = Depends(requires_authentication),
):
    with SessionLocal() as db:
        user = get_user_by_id(db, user_id)
        update_vendor_contact_email(db, vendor_id, body.contact_email)
        add_leads_data(db, body.contact_email, user.organization_id)
    return Response(status_code=200)



@router.put("/vendor/{vendor_id}", response_class=RedirectResponse)
async def edit_vendor(
    vendor_id: str, 
    body: VendorEditBody,
    user_id: str = Depends(requires_authentication)
):
    with SessionLocal() as db:
        updated_vendor = update_vendor_info(db, vendor_id, body.__dict__)
        if updated_vendor[0] is None:
            key = updated_vendor[1].split('(')[1].split(')')[0]
            value = updated_vendor[1].split(')')[1].split('(')[1]
            response_data = {"error": f'{key} with value {value} already exist.'}
            return JSONResponse(content=response_data, status_code=400)        
    return Response(status_code=200)
    

@router.get("/download-master-vendor-file")
async def download_master_vendor_file(
    request: Request,
    user_id: str = Depends(redirect_authentication),
    filter_by: str = None
):
    with SessionLocal() as db:    
        vendors = get_vendors_by_user(
            db,
            user_id
        )
        csv_file = StringIO()
        csv_writer = csv.writer(csv_file)
        header = [
            "vendor_id",                 
            "vendor_name",                
            "aliases",           
            "contact_email",       
            "created_on",      
            "updated_on",
            "user_id",             
            "organization_id",     
            "vendor_number",    
            "external_vendor_id", 
            "address_one",         
            "address_two",         
            "city",                
            "state",               
            "pincode",   
            "attention",           
            "phone",               
            "fax",                 
            "parent_vendor",
            "account",             
            "tax_id",              
            "note"
        ]
        csv_writer.writerow(header)
        records = []
        for vendor in vendors:
            vendor_details = get_vendor_by_id(db, vendor.id)
            if vendor_details:
                vendor_id = vendor_details.id
                vendor_name = vendor_details.name
                aliases = vendor_details.aliases
                contact_email = vendor_details.contact_email
                created_on = vendor_details.created_on
                updated_on = vendor_details.updated_on
                user_id = vendor_details.user_id
                organization_id = vendor_details.organization_id
                vendor_number = vendor_details.vendor_number
                external_vendor_id = vendor_details.external_vendor_id
                address_one = vendor_details.address_one
                address_two = vendor_details.address_two
                city = vendor_details.city
                state = vendor_details.state
                pincode = vendor_details.pincode
                attention = vendor_details.attention
                phone = vendor_details.phone
                fax = vendor_details.fax
                parent_vendor = vendor_details.parent_vendor
                account = vendor_details.account
                tax_id = vendor_details.tax_id
                note = vendor_details.note
                records.append([
                    vendor_id,
                    vendor_name,
                    aliases,
                    contact_email,
                    created_on,
                    updated_on,
                    user_id,
                    organization_id,
                    vendor_number,
                    external_vendor_id,
                    address_one,
                    address_two,
                    city,
                    state,
                    pincode,
                    attention,
                    phone,
                    fax,
                    parent_vendor,
                    account,
                    tax_id,
                    note
                ])
        if vendors:
            csv_writer.writerows(records)
        return StreamingResponse(
            content=iter(csv_file.getvalue()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="master-vendor-list-{format_date_american(datetime.now())}.csv"'
            },
        )
