"""
Announcement endpoints for the High School Management System API
"""

from datetime import date
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    """Payload for announcement create/update operations."""

    message: str = Field(min_length=1, max_length=400)
    expiration_date: str
    start_date: Optional[str] = None


def _is_valid_iso_date(raw_date: str) -> bool:
    """Validate YYYY-MM-DD date strings."""
    try:
        date.fromisoformat(raw_date)
        return True
    except ValueError:
        return False


def _validate_announcement_dates(start_date: Optional[str], expiration_date: str) -> None:
    """Validate date format and date order rules for announcements."""
    if not _is_valid_iso_date(expiration_date):
        raise HTTPException(status_code=400, detail="expiration_date must be in YYYY-MM-DD format")

    if start_date and not _is_valid_iso_date(start_date):
        raise HTTPException(status_code=400, detail="start_date must be in YYYY-MM-DD format")

    if start_date and start_date > expiration_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to expiration_date"
        )


def _require_signed_in_user(teacher_username: Optional[str]) -> Dict[str, Any]:
    """Validate that an authenticated teacher username exists."""
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


def _serialize_announcement(document: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB announcement documents into JSON-safe dictionaries."""
    return {
        "id": str(document["_id"]),
        "message": document.get("message", ""),
        "start_date": document.get("start_date"),
        "expiration_date": document.get("expiration_date"),
        "created_by": document.get("created_by")
    }


@router.get("", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get currently active announcements for public display."""
    today = date.today().isoformat()

    query = {
        "$and": [
            {"expiration_date": {"$gte": today}},
            {
                "$or": [
                    {"start_date": {"$exists": False}},
                    {"start_date": None},
                    {"start_date": ""},
                    {"start_date": {"$lte": today}}
                ]
            }
        ]
    }

    announcements = announcements_collection.find(query).sort(
        [("expiration_date", 1), ("_id", -1)]
    )

    return [_serialize_announcement(item) for item in announcements]


@router.get("/manage", response_model=List[Dict[str, Any]])
def list_announcements_for_management(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """List all announcements for authenticated users in the management dialog."""
    _require_signed_in_user(teacher_username)

    announcements = announcements_collection.find({}).sort(
        [("expiration_date", 1), ("_id", -1)]
    )

    return [_serialize_announcement(item) for item in announcements]


@router.post("", response_model=Dict[str, Any])
def create_announcement(payload: AnnouncementPayload, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Create a new announcement; requires authenticated teacher."""
    teacher = _require_signed_in_user(teacher_username)
    _validate_announcement_dates(payload.start_date, payload.expiration_date)

    new_announcement = {
        "message": payload.message.strip(),
        "expiration_date": payload.expiration_date,
        "start_date": payload.start_date,
        "created_by": teacher.get("username")
    }

    insert_result = announcements_collection.insert_one(new_announcement)
    created = announcements_collection.find_one({"_id": insert_result.inserted_id})

    if not created:
        raise HTTPException(status_code=500, detail="Failed to create announcement")

    return _serialize_announcement(created)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an existing announcement; requires authenticated teacher."""
    _require_signed_in_user(teacher_username)
    _validate_announcement_dates(payload.start_date, payload.expiration_date)

    if not ObjectId.is_valid(announcement_id):
        raise HTTPException(status_code=404, detail="Announcement not found")

    update_result = announcements_collection.update_one(
        {"_id": ObjectId(announcement_id)},
        {
            "$set": {
                "message": payload.message.strip(),
                "start_date": payload.start_date,
                "expiration_date": payload.expiration_date
            }
        }
    )

    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updated = announcements_collection.find_one({"_id": ObjectId(announcement_id)})
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to load updated announcement")

    return _serialize_announcement(updated)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(announcement_id: str, teacher_username: Optional[str] = Query(None)) -> Dict[str, str]:
    """Delete an existing announcement; requires authenticated teacher."""
    _require_signed_in_user(teacher_username)

    if not ObjectId.is_valid(announcement_id):
        raise HTTPException(status_code=404, detail="Announcement not found")

    delete_result = announcements_collection.delete_one({"_id": ObjectId(announcement_id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted successfully"}
