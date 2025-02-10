from app.db.models import RequestedApprover, InvitedApprover


def add_requested_approver(db, user_id, approver_id, invoice_id, expires_on):
    new_requested_approver = RequestedApprover(
        invited_by=user_id,
        invited_approver=approver_id,
        invoice_id=invoice_id,
        valid_till=expires_on
    )

    db.add(new_requested_approver)
    db.commit()
    return new_requested_approver


def is_waiting_for_approval(db, invoice_id):
    approval_request = db.query(RequestedApprover).filter_by(invoice_id=invoice_id)

    # Check if there is any approval request for particular invoice
    if not approval_request.first():
        return False

    # Check if the approval request is still valid
    # if approval_request[-1].valid_till < datetime.now():
    #     return False

    approver = db.query(InvitedApprover).filter_by(id=approval_request.first().invited_approver).first()

    return (True, f"{approver.first_name} {approver.last_name}")
