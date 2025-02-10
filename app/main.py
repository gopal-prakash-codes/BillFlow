import rollbar
from fastapi import APIRouter, Depends, FastAPI, Response, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from rollbar.contrib.fastapi import ReporterMiddleware as RollbarMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_301_MOVED_PERMANENTLY

from app.auth.utils import optional_authentication

from .admin.router import router as admin_router
from .auth.router import router as auth_router
from .config import config as global_config
from .invoices.router import router as invoices_router
from .marketing.router import router as marketing_router
from .payments.router import router as payments_router
from .users.router import router as users_router
from .vendors.router import router as vendors_router
from .approvers.router import router as approvers_router
from .manager.router import router as manager_router
from app.frontend.templates import template_response

if global_config.in_deployment:
    app = FastAPI(
        docs_url=None,
        openapi_url=None,
        redoc_url=None,
        swagger_ui_oauth2_redirect_url=None,
    )
    # Deployment specific middleware
    rollbar.init(global_config.rollbar_key, environment="production")
    app.add_middleware(RollbarMiddleware)
else:
    app = FastAPI()

app.mount("/static", StaticFiles(directory="app/frontend/static"), name="static")

app.add_middleware(SessionMiddleware, secret_key=global_config.session_secret)
app.add_middleware(CORSMiddleware, allow_origins=("*",))

app.include_router(auth_router)
app.include_router(invoices_router)
app.include_router(marketing_router)
app.include_router(payments_router)
app.include_router(users_router)
app.include_router(vendors_router)
app.include_router(admin_router)
app.include_router(approvers_router)
app.include_router(manager_router)

global_router = APIRouter()


@app.exception_handler(500)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return template_response('500.html', request=request)


@global_router.get("/health")
def get_health():
    return True


@global_router.get('/robots.txt')
def robots():
    data = """User-Agent: *
		Allow: /
		Disallow: /blog?qb-p=1
		Disallow: /blog?qb-p=2
		Disallow: /blog?qb-p=3
		Disallow: /blog?qb-p=4
		Disallow: /blog?qb-p=5
		Disallow: /blog?qb-p=6
		Disallow: /blog?qb-p=7
		Disallow: /blog?qb-p=8
		Disallow: /blog?qb-p=9
		Disallow: /blog?qb-p=10
		Disallow: /blog?qb-p=11
		Disallow: /blog?qb-p=12
		Disallow: /blog?qb-p=13
		Disallow: /blog?qb-p=14
		Disallow: /blog?qb-p=15
		Disallow: /blog?qb-c=accounting
		Disallow: /blog?qb-c=small-business
		Disallow: /blog?qb-c=tax-planning
		Disallow: /blog?qb-c=spend-management
		Disallow: /blog?qb-c=invoice-approval
		Disallow: /blog?qb-c=cash-flow
		Disallow: /blog?qb-c=pre-accounting
		Disallow: /blog?qb-c=accounts-payable
		Disallow: /blog?qb-c=process-automation

		Disallow: /login
		Disallow: /forgot-password
		Disallow: /Terms-and-condititons
		Disallow: /data-privacy"""
    return Response(content=data, media_type='text/plain')


@global_router.get("/", response_class=RedirectResponse)
def get_index(user_id: str = Depends(optional_authentication)):
    if user_id:
        return RedirectResponse("/inbox", status_code=HTTP_301_MOVED_PERMANENTLY)
    return RedirectResponse("/landing", status_code=HTTP_301_MOVED_PERMANENTLY)


app.include_router(global_router)
