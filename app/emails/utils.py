from datetime import datetime

from python_http_client import HTTPError
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Category, From, Mail, ReplyTo, To

from ..frontend.templates import template_email
from ..users.models import User
from .config import config


def send_reset_pswd_email(email: str, reset_url: str) -> None:
    message = Mail()
    message.to = [To(email=email)]
    message.from_email = From(
        email="hello@easyinvoicemanager.com",
        name="Easy Invoice Manager",
    )

    message.reply_to = ReplyTo(
        email="hello@easyinvoicemanager.com",
        name="Easy Invoice Manager",
    )

    message.template_id = "d-af503290faba4084bf74c2e64832ea35"
    message.dynamic_template_data = {"reset_url": reset_url}

    message.category = [
        Category("reset_password"),
    ]

    sendgrid_client = SendGridAPIClient(config.sendgrid_api_key)
    _ = sendgrid_client.send(message)


def send_registration_email(email: str, user: User) -> None:
    message = Mail()
    message.to = [To(email=email)]
    message.from_email = From(
        email="hello@easyinvoicemanager.com",
        name="Easy Invoice Manager",
    )

    message.reply_to = ReplyTo(
        email="hello@easyinvoicemanager.com",
        name="Easy Invoice Manager",
    )

    message.subject = "Welcome to your easyinvoicemanager account"
    message.add_content(template_email("register.txt", {"user": user}), "text/plain")

    message.category = [
        Category("registration"),
    ]

    sendgrid_client = SendGridAPIClient(config.sendgrid_api_key)
    try:
        _ = sendgrid_client.send(message)
    except HTTPError as e:
        print(e.to_dict)
        raise e


def send_invitation_email(email: str) -> None:
    message = Mail()
    message.to = [To(email=email)]
    message.from_email = From(
        email="hello@easyinvoicemanager.com",
        name="Easy Invoice Manager"
    )

    message.reply_to = ReplyTo(
        email="hello@easyinvoicemanager.com",
        name="Easy Invoice Manager"
    )

    message.subject = "Invitation For Invoice Approval"
    message.add_content(template_email("invitation.txt"), "text/plain")

    message.category = [
        Category("registration"),
    ]

    sendgrid_client = SendGridAPIClient(config.sendgrid_api_key)
    try:
        _ = sendgrid_client.send(message)
    except HTTPError as e:
        print(e.to_dict)
        raise e


def send_accountant_invitation_email(company_name: str, accountant_email: str, username: str, token: str = None) -> None:
    message = Mail()
    message.to = [To(email=accountant_email)]
    message.from_email = From(
        email="hello@easyinvoicemanager.com",
        name="Easy Invoice Manager"
    )

    message.reply_to = ReplyTo(
        email="hello@easyinvoicemanager.com",
        name="Easy Invoice Manager"
    )

    message.subject = f"Your Customer {company_name} has invited you to Easy Invoice Manager"
    message.add_content(template_email("accountant_invitation.html", context={"token": token, "username": username}), "text/html")

    message.category = [
        Category("invitation"),
    ]

    sendgrid_client = SendGridAPIClient(config.sendgrid_api_key)
    try:
        _ = sendgrid_client.send(message)
    except HTTPError as e:
        print(e.to_dict)
        raise e


def send_approver_request_email(
    email: str,
    username: str,
    invoice_number: str,
    token: str = None,
    amount_due: str = None
) -> None:
    message = Mail()
    message.to = [To(email=email)]
    message.from_email = From(
        email="hello@easyinvoicemanager.com",
        name="Easy Invoice Manager",
    )

    message.reply_to = ReplyTo(
        email="hello@easyinvoicemanager.com",
        name="Easy Invoice Manager",
    )

    message.subject = f"Your approval of invoice number #{invoice_number} is requested."
    message.add_content(
        template_email(
            "approval_request.html",
            context={"token": token, "username": username, "amount_due": amount_due}
        ), "text/html")

    message.category = [
        Category("invitation"),
    ]

    sendgrid_client = SendGridAPIClient(config.sendgrid_api_key)
    try:
        _ = sendgrid_client.send(message)
    except HTTPError as e:
        print(e.to_dict)
        raise e

def send_image_not_found_email(invoice_id: str, customer_id: str, aws_image_path: str, uploaded_on: datetime, company_name: str) -> None:
    message = Mail()
    message.to = [To(email="support@myeasyinvoicemanager.freshdesk.com")]
    message.from_email = From(
        email="hello@easyinvoicemanager.com",
        name="Easy Invoice Manager",
    )

    message.reply_to = ReplyTo(
        email="hello@easyinvoicemanager.com",
        name="Easy Invoice Manager",
    )

    message.subject = f"Trouble ticket for Image Not Found for invoice: {invoice_id}"
    message.add_content(template_email("trouble_ticket.txt", context={"invoice_id": invoice_id, "customer_id": customer_id, "uploaded_on": uploaded_on, "aws_image_path": aws_image_path, "company_name": company_name}), "text/plain")

    message.category = [
        Category("Trouble"),
    ]

    sendgrid_client = SendGridAPIClient(config.sendgrid_api_key)
    try:
        _ = sendgrid_client.send(message)
    except HTTPError as e:
        print(e.to_dict)
        raise e
    

def send_ap_staff_email(email: str) -> None:
    message = Mail()
    message.to = [To(email=email)]
    message.from_email = From(
        email="hello@easyinvoicemanager.com",
        name="Easy Invoice Manager"
    )

    message.reply_to = ReplyTo(
        email="hello@easyinvoicemanager.com",
        name="Easy Invoice Manager"
    )

    message.subject = "Secure Your AP Role at [Your Company Name] Invitation from [Manager's Name]"
    message.add_content(template_email("ap_staff_invite.html"), "text/html")

    message.category = [
        Category("invitation"),
    ]
    
    sendgrid_client = SendGridAPIClient(config.sendgrid_api_key)
    try:
        _ = sendgrid_client.send(message)
    except HTTPError as e:
        print(e.to_dict)
        raise e
