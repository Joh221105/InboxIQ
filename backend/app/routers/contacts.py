from __future__ import annotations

from typing import get_args
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.auth import UserClaims, get_current_user
from app.core.errors import NotFoundError
from app.db.contact_tags import delete_tag, list_user_tags, update_tag
from app.models.contact_tag import (
    ContactsGrouped,
    ContactTag,
    ContactTagCreate,
    ContactTagUpdate,
    CreateContactResponse,
    TagType,
)
from app.models.job import JobStatusResponse
from app.services.contact_tags import CONTACT_TAG_JOBS, tag_contact

router = APIRouter(tags=["contacts"])


@router.post("/contacts")
async def post_contact(
    body: ContactTagCreate,
    claims: UserClaims = Depends(get_current_user),
) -> CreateContactResponse:
    return await tag_contact(claims.user_id, body)


@router.get("/contacts")
async def get_contacts(claims: UserClaims = Depends(get_current_user)) -> ContactsGrouped:
    grouped: dict[str, list[ContactTag]] = {tag_type: [] for tag_type in get_args(TagType)}
    for tag in await list_user_tags(claims.user_id):
        grouped[tag.tag].append(tag)
    return ContactsGrouped(**grouped)


@router.delete("/contacts/{tag_id}", status_code=204, response_model=None)
async def delete_contact(
    tag_id: UUID,
    claims: UserClaims = Depends(get_current_user),
) -> None:
    if not await delete_tag(tag_id, claims.user_id):
        raise NotFoundError("Contact tag not found.")


@router.patch("/contacts/{tag_id}")
async def patch_contact(
    tag_id: UUID,
    body: ContactTagUpdate,
    claims: UserClaims = Depends(get_current_user),
) -> ContactTag:
    updated = await update_tag(tag_id, claims.user_id, body.changes())
    if updated is None:
        raise NotFoundError("Contact tag not found.")
    return updated


@router.get("/contacts/jobs/{job_id}")
async def get_contact_job(
    job_id: str,
    claims: UserClaims = Depends(get_current_user),
) -> JobStatusResponse:
    return JobStatusResponse.from_job(CONTACT_TAG_JOBS.get_for_user(job_id, claims.user_id))
