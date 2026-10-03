from __future__ import annotations

import random
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.auth import UserClaims, get_current_user
from app.db.contact_tags import (
    UniqueViolation,
    apply_retroactive_sync,
    count_emails_for_identifier,
    create_tag,
    delete_tag,
    list_user_tags,
    update_tag,
)
from app.models.contact_tag import (
    ContactsGrouped,
    ContactTag,
    ContactTagCreate,
    ContactTagUpdate,
    CreateContactResponse,
)
from app.models.job import JobStatusResponse
from app.services.contact_tags import (
    CONTACT_TAG_JOBS,
    CUSTOM_PALETTE,
    DEFAULT_COLORS,
    SYNC_THRESHOLD,
    VALID_TAG_TYPES,
    apply_retroactive_async,
    normalize_identifier,
)

router = APIRouter(tags=["contacts"])


@router.post("/contacts", response_model=CreateContactResponse)
async def post_contact(
    body: ContactTagCreate,
    claims: UserClaims = Depends(get_current_user),
) -> CreateContactResponse:
    try:
        identifier = normalize_identifier(body.identifier)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if body.tag not in VALID_TAG_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"tag must be one of: {', '.join(sorted(VALID_TAG_TYPES))}",
        )

    if body.tag == "custom" and not body.custom_label:
        raise HTTPException(status_code=422, detail="custom_label is required for custom tags")

    if body.color:
        color = body.color
    elif body.tag in DEFAULT_COLORS:
        color = DEFAULT_COLORS[body.tag]
    else:
        color = random.choice(CUSTOM_PALETTE)

    try:
        tag = await create_tag(
            user_id=claims.user_id,
            identifier=identifier,
            tag=body.tag,
            custom_label=body.custom_label,
            color=color,
        )
    except UniqueViolation as exc:
        raise HTTPException(status_code=409, detail={"reason": "duplicate"}) from exc

    count = await count_emails_for_identifier(claims.user_id, identifier)

    if count <= SYNC_THRESHOLD:
        await apply_retroactive_sync(tag.id, claims.user_id, identifier)
        return CreateContactResponse(tag=tag, retroactive_count=count, job_id=None)
    else:
        job_id = await apply_retroactive_async(tag.id, claims.user_id, identifier)
        return CreateContactResponse(tag=tag, retroactive_count=count, job_id=job_id)


@router.get("/contacts", response_model=ContactsGrouped)
async def get_contacts(
    claims: UserClaims = Depends(get_current_user),
) -> ContactsGrouped:
    tags = await list_user_tags(claims.user_id)
    grouped: dict[str, list[ContactTag]] = {
        "professor": [],
        "friend": [],
        "recruiter": [],
        "custom": [],
    }
    for tag in tags:
        if tag.tag in grouped:
            grouped[tag.tag].append(tag)
    return ContactsGrouped(**grouped)


@router.delete("/contacts/{tag_id}")
async def delete_contact(
    tag_id: UUID,
    claims: UserClaims = Depends(get_current_user),
) -> Response:
    deleted = await delete_tag(tag_id, claims.user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact tag not found")
    return Response(status_code=204)


@router.patch("/contacts/{tag_id}", response_model=ContactTag)
async def patch_contact(
    tag_id: UUID,
    body: ContactTagUpdate,
    claims: UserClaims = Depends(get_current_user),
) -> ContactTag:
    changes: dict[str, object] = {}
    if body.custom_label is not None:
        changes["custom_label"] = body.custom_label
    if body.color is not None:
        changes["color"] = body.color
    if not changes:
        raise HTTPException(status_code=422, detail="No updatable fields provided")
    updated = await update_tag(tag_id, claims.user_id, changes)
    if updated is None:
        raise HTTPException(status_code=404, detail="Contact tag not found")
    return updated


@router.get("/contacts/jobs/{job_id}")
async def get_contact_job(
    job_id: str,
    claims: UserClaims = Depends(get_current_user),
) -> JobStatusResponse:
    return JobStatusResponse.from_job(CONTACT_TAG_JOBS.get_for_user(job_id, claims.user_id))
