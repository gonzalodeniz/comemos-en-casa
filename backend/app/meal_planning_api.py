"""Authenticated read and write endpoints for meal planning."""

import hashlib
import json
import logging
from contextlib import contextmanager
from datetime import date, datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import ActiveSession, get_active_session, require_csrf
from app.database import get_database_session
from app.models import FoodLabel, MealAssignment
from app.meal_planning import repetition_dates

router = APIRouter(prefix="/api/v1", tags=["meal-planning"])
logger = logging.getLogger(__name__)
MEAL_PLANNING_WRITE_LOCK = 1128481603


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
                }
            ),
            "resulting_label": (
                {"id": str(label.id), "code": label.code, "name": label.name}
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
) -> dict[str, list[dict[str, str]]]:
    labels = db.scalars(select(FoodLabel).order_by(FoodLabel.code)).all()
    return {
        "labels": [
            {"id": str(label.id), "code": label.code, "name": label.name}
            for label in labels
        ]
    }


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
