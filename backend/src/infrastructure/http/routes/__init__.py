from fastapi import FastAPI

from .admin_actions import router as admin_actions_router
from .admin_dashboard import router as admin_dashboard_router
from .admin_pages import router as admin_pages_router
from .admin_settings import router as admin_settings_router
from .admin_users import router as admin_users_router
from .auth import router as auth_router
from .beacon import router as beacon_router
from .callback import router as callback_router
from .feedback import router as feedback_router
from .health import router as health_router
from .public_pages import router as public_pages_router
from .purchase import router as purchase_router


def setup_router(app: FastAPI) -> None:
    app.include_router(health_router)
    app.include_router(purchase_router)
    app.include_router(beacon_router)
    app.include_router(callback_router)
    app.include_router(feedback_router)
    app.include_router(auth_router)
    app.include_router(public_pages_router)
    app.include_router(admin_dashboard_router)
    app.include_router(admin_actions_router)
    app.include_router(admin_users_router)
    app.include_router(admin_pages_router)
    app.include_router(admin_settings_router)
