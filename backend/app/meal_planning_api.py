"""Authenticated read and write endpoints for meal planning."""

import asyncio
import hashlib
import json
import logging
import os
import unicodedata
from pathlib import Path
from contextlib import contextmanager
from datetime import date, datetime
from functools import wraps
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import ActiveSession, get_active_session, require_csrf
from app.database import get_database_session
from app.models import FoodLabel, MealAssignment
from app.meal_planning import repetition_dates
from app.food_images import InvalidFoodImage, async_publication_lock, crop_to_webp, publish_temporary, save_temporary, temporary_path
from app.safe_image_url import UnsafeImageURL, safe_fetch_image

router = APIRouter(prefix="/api/v1", tags=["meal-planning"])
logger = logging.getLogger(__name__)
MEAL_PLANNING_WRITE_LOCK = 1128481603
DATA_ROOT = Path(os.getenv("APP_DATA_ROOT", "/app/data"))


def serialized_image_publication(function):
    @wraps(function)
    async def wrapped(*args, **kwargs):
        async with async_publication_lock(DATA_ROOT):
            return await function(*args, **kwargs)
    return wrapped


def _managed_food_image_path(relative_path: str) -> Path | None:
    """Accept only opaque files directly inside the managed directory."""
    try:
        relative = Path(relative_path)
        if len(relative.parts) != 2 or relative.parts[0] != "comidas":
            return None
        name = relative.parts[1]
        if len(name) != 37 or not name.endswith(".webp") or any(c not in "0123456789abcdef" for c in name[:32]):
            return None
        directory = DATA_ROOT / "comidas"
        path = directory / name
        if directory.is_symlink() or path.is_symlink():
            return None
        return path
    except (OSError, RuntimeError, ValueError):
        return None


def _food_image_url(label: FoodLabel) -> str | None:
    if not label.image_path:
        return None
    version = hashlib.sha256(label.image_path.encode("utf-8")).hexdigest()
    return f"/food-labels/{label.id}/image?v={version}"


def _remove_food_image(relative_path: str) -> None:
    path = _managed_food_image_path(relative_path)
    if path is None:
        logger.warning("food_image_cleanup_rejected_path")
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.warning("food_image_cleanup_failed")


def canonical_label_name(value: str) -> tuple[str, str]:
    name = unicodedata.normalize("NFC", value).strip()
    canonical = name.casefold()
    if not name or len(name) > 100:
        raise HTTPException(status_code=422, detail="Name must contain 1 to 100 characters")
    return name, canonical


def _is_duplicate_label_error(error: IntegrityError) -> bool:
    original = error.orig
    constraint = getattr(getattr(original, "diag", None), "constraint_name", None)
    if constraint == "uq_food_labels_name_canonical":
        return True
    return "food_labels.name_canonical" in str(original)


class Repetition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interval_weeks: StrictInt = Field(gt=0)
    end_date: date


class MealPlanningOperation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["assign", "delete"]
    start_date: date
    slot: Literal["lunch", "dinner"]
    label_id: UUID
    repeat: Repetition | None = None
    confirmed: bool = False
    preview_token: str | None = None

    @model_validator(mode="after")
    def reject_datetime_inputs(self):
        for name in ("start_date",):
            value = getattr(self, name)
            if isinstance(value, datetime):
                raise ValueError(f"{name} must be a calendar date")
        return self


def occurrence_dates(operation: MealPlanningOperation) -> list[date]:
    if operation.repeat is None:
        return [operation.start_date]
    try:
        return repetition_dates(
            operation.start_date,
            interval_weeks=operation.repeat.interval_weeks,
            end_date=operation.repeat.end_date,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


def _operation_data(operation: MealPlanningOperation) -> dict[str, object]:
    return {
        "action": operation.action,
        "start_date": operation.start_date.isoformat(),
        "slot": operation.slot,
        "label_id": str(operation.label_id),
        "repeat": (
            None
            if operation.repeat is None
            else {
                "interval_weeks": operation.repeat.interval_weeks,
                "end_date": operation.repeat.end_date.isoformat(),
            }
        ),
    }


def build_preview(
    db: Session, operation: MealPlanningOperation
) -> dict[str, object]:
    dates = occurrence_dates(operation)
    label = db.get(FoodLabel, operation.label_id)
    if label is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="label_id does not identify a catalog label",
        )

    rows = db.scalars(
        select(MealAssignment).where(
            MealAssignment.date.in_(dates), MealAssignment.slot == operation.slot
        )
    ).all()
    by_date = {row.date: row for row in rows}
    entries: list[dict[str, object]] = []
    changes: list[str] = []
    snapshot: list[dict[str, str | None]] = []
    requires_confirmation = False
    for occurrence in dates:
        current = by_date.get(occurrence)
        current_label = (
            db.get(FoodLabel, current.label_id) if current is not None else None
        )
        if operation.action == "assign":
            if current is None:
                change = "assign"
            elif current.label_id == operation.label_id:
                change = "unchanged"
            else:
                change = "replace"
                requires_confirmation = True
        elif current is not None and current.label_id == operation.label_id:
            change = "delete"
            requires_confirmation = True
        else:
            change = "no_op"

        if change not in {"unchanged", "no_op"}:
            changes.append(occurrence.isoformat())
        entry: dict[str, object] = {
            "date": occurrence.isoformat(),
            "slot": operation.slot,
            "change": change,
            "current_label": (
                None
                if current_label is None
                else {
                    "id": str(current_label.id),
                    "code": current_label.code,
                    "name": current_label.name,
                    "image_url": _food_image_url(current_label),
                }
            ),
            "resulting_label": (
                {"id": str(label.id), "code": label.code, "name": label.name,
                 "image_url": _food_image_url(label)}
                if operation.action == "assign"
                else None
            ),
        }
        entries.append(entry)
        snapshot.append(
            {
                "date": occurrence.isoformat(),
                "assignment_id": str(current.id) if current is not None else None,
                "label_id": str(current.label_id) if current is not None else None,
            }
        )

    token_source = json.dumps(
        {"operation": _operation_data(operation), "snapshot": snapshot},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    preview_token = hashlib.sha256(token_source).hexdigest()
    return {
        "operation": _operation_data(operation),
        "dates": entries,
        "changed_dates": changes,
        "change_count": len(changes),
        "changed_count": len(changes),
        "requires_confirmation": requires_confirmation,
        "preview_token": preview_token,
    }


@contextmanager
def serialize_meal_planning_writes(db: Session):
    if db.get_bind().dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": MEAL_PLANNING_WRITE_LOCK},
        )
    yield


def _operation_response(
    status_code: int, preview: dict[str, object], *, detail: str
) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={"message": detail, "preview": preview},
    )


def canary_today() -> date:
    return datetime.now(ZoneInfo("Atlantic/Canary")).date()


@router.get("/food-labels")
async def list_food_labels(
    _active_session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, list[dict[str, str | None]]]:
    labels = db.scalars(select(FoodLabel).order_by(FoodLabel.code)).all()
    return {
        "labels": [
            {"id": str(label.id), "code": label.code, "name": label.name,
             "image_url": _food_image_url(label)}
            for label in labels
        ]
    }


@router.post("/food-labels", status_code=201)
@serialized_image_publication
async def create_food_label(payload: dict[str, str], request: Request,
    active_session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session)):
    require_csrf(request, active_session)
    if set(payload) - {"name", "image_token"} or not isinstance(payload.get("name"), str):
        raise HTTPException(status_code=422, detail="Invalid food label")
    name, canonical = canonical_label_name(payload["name"])
    if db.scalar(select(FoodLabel).where(FoodLabel.name_canonical == canonical)):
        raise HTTPException(status_code=409, detail="Food already exists")
    image_path = publish_temporary(DATA_ROOT, active_session.session.id, payload["image_token"]) if payload.get("image_token") else None
    if payload.get("image_token") and image_path is None:
        raise HTTPException(status_code=422, detail="Prepared image expired")
    label = FoodLabel(code=f"custom-{os.urandom(12).hex()}", name=name, image_path=image_path)
    db.add(label)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if _is_duplicate_label_error(error):
            raise HTTPException(status_code=409, detail="Food already exists") from error
        raise
    except Exception:
        db.rollback()
        raise
    db.refresh(label)
    return {"id": str(label.id), "code": label.code, "name": label.name,
            "image_url": _food_image_url(label)}


@router.patch("/food-labels/{label_id}")
@serialized_image_publication
async def update_food_label(label_id: UUID, payload: dict[str, object], request: Request,
    active_session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session)):
    require_csrf(request, active_session)
    if (set(payload) - {"name", "image_token", "remove_image"}
        or not isinstance(payload.get("name"), str)
        or ("image_token" in payload and not isinstance(payload["image_token"], str))
        or ("remove_image" in payload and not isinstance(payload["remove_image"], bool))):
        raise HTTPException(status_code=422, detail="Invalid food label")
    label = db.get(FoodLabel, label_id)
    if label is None:
        raise HTTPException(status_code=404, detail="Food not found")
    name, canonical = canonical_label_name(payload["name"])
    if db.scalar(select(FoodLabel).where(FoodLabel.name_canonical == canonical, FoodLabel.id != label_id)):
        raise HTTPException(status_code=409, detail="Food already exists")
    new_path = publish_temporary(DATA_ROOT, active_session.session.id, payload["image_token"]) if payload.get("image_token") else None
    if payload.get("image_token") and new_path is None:
        raise HTTPException(status_code=422, detail="Prepared image expired")
    old_path = label.image_path
    label.name = name
    label.name_canonical = canonical
    if new_path:
        label.image_path = new_path
    elif payload.get("remove_image") is True:
        label.image_path = None
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if _is_duplicate_label_error(error):
            raise HTTPException(status_code=409, detail="Food already exists") from error
        raise
    except Exception:
        db.rollback()
        raise
    if old_path and label.image_path != old_path:
        _remove_food_image(old_path)
    return {"id": str(label.id), "code": label.code, "name": label.name, "image_url": _food_image_url(label)}


@router.post("/food-labels/images/prepare")
async def prepare_food_image(payload: dict[str, object], request: Request,
    active_session: ActiveSession = Depends(get_active_session)):
    require_csrf(request, active_session)
    if set(payload) != {"data_url", "crop"} or not isinstance(payload["data_url"], str) or not isinstance(payload["crop"], dict):
        raise HTTPException(status_code=422, detail="Invalid image payload")
    try:
        webp = crop_to_webp(payload["data_url"], payload["crop"])
        token = save_temporary(DATA_ROOT, active_session.session.id, webp)
    except InvalidFoodImage as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"image_token": token, "expires_in_seconds": 3600}


@router.post("/food-labels/images/import-url")
async def import_food_image_url(payload: dict[str, str], request: Request,
    _active_session: ActiveSession = Depends(get_active_session)):
    require_csrf(request, _active_session)
    if set(payload) != {"url"} or not isinstance(payload.get("url"), str):
        raise HTTPException(status_code=422, detail="Invalid image URL")
    try:
        image_bytes, _final_url = await asyncio.to_thread(safe_fetch_image, payload["url"])
        from PIL import Image, UnidentifiedImageError
        from PIL.Image import DecompressionBombError
        import io, base64
        with Image.open(io.BytesIO(image_bytes)) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"} or getattr(image, "n_frames", 1) != 1:
                raise InvalidFoodImage("Only static JPG, PNG, or WebP images are supported")
            if image.width * image.height > 5_000_000:
                raise InvalidFoodImage("Image exceeds 5 megapixels")
            mime = {"JPEG":"image/jpeg", "PNG":"image/png", "WEBP":"image/webp"}[image.format]
        return {"data_url": f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"}
    except UnsafeImageURL as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except (InvalidFoodImage, UnidentifiedImageError, OSError, DecompressionBombError) as error:
        raise HTTPException(status_code=422, detail="URL does not contain a supported image") from error


@router.get("/food-labels/{label_id}/deletion-impact")
async def food_label_impact(label_id: UUID, _active: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session)):
    label = db.get(FoodLabel, label_id)
    if label is None: raise HTTPException(status_code=404, detail="Food not found")
    return {"assignment_count": len(db.scalars(select(MealAssignment).where(MealAssignment.label_id == label_id)).all()), "recipe_count": 0}


@router.delete("/food-labels/{label_id}", status_code=204)
async def delete_food_label(label_id: UUID, request: Request, response: Response,
    active_session: ActiveSession = Depends(get_active_session), db: Session = Depends(get_database_session)):
    require_csrf(request, active_session)
    with serialize_meal_planning_writes(db):
        label = db.get(FoodLabel, label_id)
        if label is None: raise HTTPException(status_code=404, detail="Food not found")
        db.query(MealAssignment).filter(MealAssignment.label_id == label_id).delete(synchronize_session=False)
        old_path = label.image_path
        db.delete(label)
        db.commit()
    if old_path:
        _remove_food_image(old_path)
    response.status_code = 204


@router.get("/food-labels/{label_id}/image")
async def get_food_label_image(label_id: UUID, response: Response,
    _active: ActiveSession = Depends(get_active_session), db: Session = Depends(get_database_session)):
    from fastapi.responses import FileResponse
    label = db.get(FoodLabel, label_id)
    if label is None or not label.image_path: raise HTTPException(status_code=404, detail="Image not found")
    path = _managed_food_image_path(label.image_path)
    if path is None or not path.is_file(): raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, media_type="image/webp", headers={"Cache-Control":"private, max-age=3600"})


@router.get("/meal-planning")
async def get_meal_planning(
    start_date: date = Query(...),
    end_date: date = Query(...),
    _active_session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, object]:
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="end_date must be on or after start_date",
        )

    assignments = db.execute(
        select(MealAssignment, FoodLabel)
        .join(FoodLabel, MealAssignment.label_id == FoodLabel.id)
        .where(
            MealAssignment.date >= start_date,
            MealAssignment.date <= end_date,
        )
        .order_by(MealAssignment.date, MealAssignment.slot)
    ).all()

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "today": canary_today().isoformat(),
        "timezone": "Atlantic/Canary",
        "assignments": [
            {
                "id": str(assignment.id),
                "date": assignment.date.isoformat(),
                "slot": assignment.slot,
                "label": {
                    "id": str(label.id),
                    "code": label.code,
                    "name": label.name,
                    "image_url": _food_image_url(label),
                },
            }
            for assignment, label in assignments
        ],
    }


@router.post("/meal-planning/preview")
async def preview_meal_planning_operation(
    operation: MealPlanningOperation,
    request: Request,
    active_session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, object]:
    require_csrf(request, active_session)
    return build_preview(db, operation)


@router.post("/meal-planning/operations")
async def apply_meal_planning_operation(
    operation: MealPlanningOperation,
    request: Request,
    active_session: ActiveSession = Depends(get_active_session),
    db: Session = Depends(get_database_session),
) -> dict[str, object]:
    require_csrf(request, active_session)
    try:
        with serialize_meal_planning_writes(db):
            preview = build_preview(db, operation)
            expected_token = operation.preview_token
            current_token = str(preview["preview_token"])
            if expected_token is not None and expected_token != current_token:
                _operation_response(
                    status.HTTP_409_CONFLICT,
                    preview,
                    detail="Planning changed since the preview; review the updated preview",
                )
            if preview["requires_confirmation"] and (
                not operation.confirmed or expected_token is None
            ):
                _operation_response(
                    status.HTTP_409_CONFLICT,
                    preview,
                    detail="This operation requires confirmation of the current preview",
                )

            dates = occurrence_dates(operation)
            label_id = operation.label_id
            rows = db.scalars(
                select(MealAssignment).where(
                    MealAssignment.date.in_(dates),
                    MealAssignment.slot == operation.slot,
                )
            ).all()
            by_date = {row.date: row for row in rows}
            changed_dates: list[str] = []
            for occurrence in dates:
                current = by_date.get(occurrence)
                if operation.action == "assign":
                    if current is None:
                        db.add(
                            MealAssignment(
                                date=occurrence,
                                slot=operation.slot,
                                label_id=label_id,
                            )
                        )
                        changed_dates.append(occurrence.isoformat())
                    elif current.label_id != label_id:
                        current.label_id = label_id
                        changed_dates.append(occurrence.isoformat())
                elif current is not None and current.label_id == label_id:
                    db.delete(current)
                    changed_dates.append(occurrence.isoformat())
            db.commit()
            return {
                "operation": _operation_data(operation),
                "changed_dates": changed_dates,
                "changed_count": len(changed_dates),
            }
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("meal_planning_operation_failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Meal-planning operation could not be saved",
        ) from error
