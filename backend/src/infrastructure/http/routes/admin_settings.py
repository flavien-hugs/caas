"""
Runtime configuration routes — all guarded by ``MANAGE_SETTINGS``.

Sections (``general``, ``smtp``, ``kkiapay``, ``cinetpay``, ``sms``) are edited
independently. Secret fields are never returned: each section response carries
``values`` (non-secret, effective after DB-over-env resolution) and ``secrets``
(per-field booleans telling whether a value is configured). On update, a secret
left blank keeps the stored one.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ValidationError

from src.application.config import ResolvedConfig
from src.application.use_cases import (
    GetConfiguration,
    SmtpNotConfigured,
    TestSms,
    TestSmtp,
    UnknownConfigSection,
    UpdateConfigurationSection,
)
from src.domain import ConfigSection, Permission
from src.infrastructure.config.settings import settings
from src.infrastructure.http.deps import (
    get_configuration_use_case,
    resolved_config,
    test_sms_use_case,
    test_smtp_use_case,
    update_configuration_use_case,
)
from src.infrastructure.http.rbac import require_permission

router = APIRouter(
    prefix="/admin/settings",
    tags=["admin"],
    dependencies=[Depends(require_permission(Permission.MANAGE_SETTINGS))],
)


class SectionConfigResponse(BaseModel):
    values: dict[str, Any]
    secrets: dict[str, bool] = Field(default_factory=dict)


class SmtpTestBody(BaseModel):
    to: str = Field(min_length=3, max_length=320)


class SmsTestBody(BaseModel):
    to: str = Field(min_length=3, max_length=40)
    body: str | None = Field(default=None, max_length=480)


@router.get("", response_model=dict[str, SectionConfigResponse])
async def get_all_settings(
    use_case: GetConfiguration = Depends(get_configuration_use_case),
) -> dict[str, SectionConfigResponse]:
    data = await use_case.execute()
    return {name: SectionConfigResponse(**section) for name, section in data.items()}


@router.get("/{section}", response_model=SectionConfigResponse)
async def get_section(
    section: ConfigSection,
    use_case: GetConfiguration = Depends(get_configuration_use_case),
) -> SectionConfigResponse:
    data = await use_case.execute()
    return SectionConfigResponse(**data[section.value])


@router.put("/{section}", response_model=SectionConfigResponse)
async def update_section(
    section: ConfigSection,
    body: dict[str, Any],
    use_case: UpdateConfigurationSection = Depends(update_configuration_use_case),
) -> SectionConfigResponse:
    # CinetPay is a scaffold: its verify_payment returns PENDING, so selecting
    # it would silently never confirm a payment. Forbid activating it in
    # production until the gateway integration is complete (dev/staging may
    # still select it to exercise the wiring).
    if section == ConfigSection.GENERAL and body.get("payment_provider") == "cinetpay" and settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CinetPay n'est pas encore opérationnel (intégration en cours) — sélection interdite en production.",
        )
    try:
        result = await use_case.execute(section, body)
    except UnknownConfigSection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"unknown section: {section}") from None
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()) from e
    return SectionConfigResponse(**result)


@router.post("/smtp/test", status_code=status.HTTP_204_NO_CONTENT)
async def test_smtp(
    body: SmtpTestBody,
    cfg: ResolvedConfig = Depends(resolved_config),
    use_case: TestSmtp = Depends(test_smtp_use_case),
) -> None:
    try:
        await use_case.execute(cfg.smtp, body.to)
    except SmtpNotConfigured:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SMTP non configuré.") from None
    except Exception as e:  # network / auth failure from the SMTP server
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Échec de l'envoi: {e}") from e


@router.post("/sms/test", status_code=status.HTTP_204_NO_CONTENT)
async def test_sms(
    body: SmsTestBody,
    use_case: TestSms = Depends(test_sms_use_case),
) -> None:
    try:
        await use_case.execute(body.to, body.body)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Échec de l'envoi: {e}") from e
