from __future__ import annotations

from typing import Any
from unittest import result

from bson import ObjectId
from docx import document
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import database
from pymongo.errors import ServerSelectionTimeoutError

from backend.config import MONGODB_DB_NAME, MONGODB_COLLECTION_NAME, MONGODB_URI

_client = None
_db = None
_in_memory_profiles: list[dict[str, Any]] = []
_in_memory_test_results: list[dict[str, Any]] = []


async def get_database():
    global _client, _db

    if _db is not None:
        return _db

    try:
        _client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        _db = _client[MONGODB_DB_NAME]
        await _db.command("ping")
        return _db
    except Exception as exc:  # pragma: no cover - fallback for local development without MongoDB
        _client = None
        _db = None
        print(f"[MongoDB] Connection failed: {exc}. Falling back to in-memory storage.")
        return None


def serialize_mongo_document(document: dict[str, Any] | None) -> dict[str, Any] | None:
    if document is None:
        return None

    serialized = dict(document)
    if "_id" in serialized and isinstance(serialized["_id"], ObjectId):
        serialized["_id"] = str(serialized["_id"])
    return serialized


async def get_users_collection():
    database = await get_database()
    if database is None:
        return None
    return database[MONGODB_COLLECTION_NAME]


async def get_feature_collection(collection_name: str):
    database = await get_database()
    if database is None:
        return None
    return database[collection_name]


_in_memory_study_tasks: list[dict[str, Any]] = []
_in_memory_quiz_results: list[dict[str, Any]] = []
_in_memory_interview_bank_progress: list[dict[str, Any]] = []
_in_memory_roadmaps: list[dict[str, Any]] = []
_in_memory_notes: list[dict[str, Any]] = []
_in_memory_achievements: list[dict[str, Any]] = []


async def fetch_study_tasks(user_id: str) -> list[dict[str, Any]]:
    collection = await get_feature_collection("study_tasks")
    if collection is None:
        return [task for task in _in_memory_study_tasks if task.get("user_id") == user_id]

    try:
        return [serialize_mongo_document(doc) async for doc in collection.find({"user_id": user_id}).sort("deadline", 1)]
    except Exception as exc:
        print(f"[MongoDB] Study tasks read failed: {exc}")
        return [task for task in _in_memory_study_tasks if task.get("user_id") == user_id]


async def store_study_task(user_id: str, task_data: dict[str, Any]) -> dict[str, Any]:
    collection = await get_feature_collection("study_tasks")
    document = {"user_id": user_id, **task_data}
    if collection is None:
        _in_memory_study_tasks.append(document)
        return document

    try:
        result = await collection.insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document
    except Exception as exc:
        print(f"[MongoDB] Study task save failed: {exc}")
        _in_memory_study_tasks.append(document)
        return document


async def update_study_task(user_id: str, task_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    collection = await get_feature_collection("study_tasks")
    if collection is None:
        for index, task in enumerate(_in_memory_study_tasks):
            if task.get("user_id") == user_id and task.get("task_id") == task_id:
                _in_memory_study_tasks[index].update(updates)
                return _in_memory_study_tasks[index]
        return None

    try:
        result = await collection.update_one({"user_id": user_id, "task_id": task_id}, {"$set": updates})
        if result.matched_count == 0:
            return None
        return await collection.find_one({"user_id": user_id, "task_id": task_id})
    except Exception as exc:
        print(f"[MongoDB] Study task update failed: {exc}")
        return None


async def delete_study_task(user_id: str, task_id: str) -> bool:
    collection = await get_feature_collection("study_tasks")
    if collection is None:
        before = len(_in_memory_study_tasks)
        _in_memory_study_tasks[:] = [task for task in _in_memory_study_tasks if not (task.get("user_id") == user_id and task.get("task_id") == task_id)]
        return len(_in_memory_study_tasks) < before

    try:
        result = await collection.delete_one({"user_id": user_id, "task_id": task_id})
        return result.deleted_count > 0
    except Exception as exc:
        print(f"[MongoDB] Study task delete failed: {exc}")
        return False


async def fetch_quiz_results(user_id: str) -> list[dict[str, Any]]:
    collection = await get_feature_collection("quiz_results")
    if collection is None:
        return [result for result in _in_memory_quiz_results if result.get("user_id") == user_id]

    try:
        return [serialize_mongo_document(doc) async for doc in collection.find({"user_id": user_id}).sort("submitted_at", -1)]
    except Exception as exc:
        print(f"[MongoDB] Quiz results read failed: {exc}")
        return [result for result in _in_memory_quiz_results if result.get("user_id") == user_id]


async def store_quiz_result(user_id: str, result_data: dict[str, Any]) -> dict[str, Any]:
    collection = await get_feature_collection("quiz_results")
    document = {"user_id": user_id, **result_data}
    if collection is None:
        _in_memory_quiz_results.append(document)
        return document

    try:
        result = await collection.insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document
    except Exception as exc:
        print(f"[MongoDB] Quiz result save failed: {exc}")
        _in_memory_quiz_results.append(document)
        return document


async def fetch_interview_bank_progress(user_id: str) -> list[dict[str, Any]]:
    collection = await get_feature_collection("interview_bank_progress")
    if collection is None:
        return [entry for entry in _in_memory_interview_bank_progress if entry.get("user_id") == user_id]

    try:
        return [serialize_mongo_document(doc) async for doc in collection.find({"user_id": user_id})]
    except Exception as exc:
        print(f"[MongoDB] Interview bank progress read failed: {exc}")
        return [entry for entry in _in_memory_interview_bank_progress if entry.get("user_id") == user_id]


async def upsert_interview_bank_progress(user_id: str, progress_data: dict[str, Any]) -> dict[str, Any]:
    collection = await get_feature_collection("interview_bank_progress")
    document = {"user_id": user_id, **progress_data}
    if collection is None:
        for index, entry in enumerate(_in_memory_interview_bank_progress):
            if entry.get("user_id") == user_id and entry.get("question_id") == progress_data.get("question_id"):
                _in_memory_interview_bank_progress[index].update(progress_data)
                return _in_memory_interview_bank_progress[index]
        _in_memory_interview_bank_progress.append(document)
        return document

    try:
        await collection.update_one(
            {"user_id": user_id, "question_id": progress_data.get("question_id")},
            {"$set": document},
            upsert=True,
        )
        return document
    except Exception as exc:
        print(f"[MongoDB] Interview bank progress save failed: {exc}")
        return document


async def fetch_roadmaps(user_id: str) -> list[dict[str, Any]]:
    collection = await get_feature_collection("roadmaps")
    if collection is None:
        return [roadmap for roadmap in _in_memory_roadmaps if roadmap.get("user_id") == user_id]

    try:
        return [serialize_mongo_document(doc) async for doc in collection.find({"user_id": user_id}).sort("updated_at", -1)]
    except Exception as exc:
        print(f"[MongoDB] Roadmaps read failed: {exc}")
        return [roadmap for roadmap in _in_memory_roadmaps if roadmap.get("user_id") == user_id]


async def store_roadmap(user_id: str, roadmap_data: dict[str, Any]) -> dict[str, Any]:
    collection = await get_feature_collection("roadmaps")
    document = {"user_id": user_id, **roadmap_data}
    if collection is None:
        _in_memory_roadmaps.append(document)
        return document

    try:
        result = await collection.insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document
    except Exception as exc:
        print(f"[MongoDB] Roadmap save failed: {exc}")
        _in_memory_roadmaps.append(document)
        return document


async def update_roadmap(user_id: str, roadmap_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    collection = await get_feature_collection("roadmaps")
    if collection is None:
        for index, roadmap in enumerate(_in_memory_roadmaps):
            if roadmap.get("user_id") == user_id and roadmap.get("roadmap_id") == roadmap_id:
                _in_memory_roadmaps[index].update(updates)
                return _in_memory_roadmaps[index]
        return None

    try:
        result = await collection.update_one({"user_id": user_id, "roadmap_id": roadmap_id}, {"$set": updates})
        if result.matched_count == 0:
            return None
        return await collection.find_one({"user_id": user_id, "roadmap_id": roadmap_id})
    except Exception as exc:
        print(f"[MongoDB] Roadmap update failed: {exc}")
        return None


async def fetch_notes(user_id: str) -> list[dict[str, Any]]:
    collection = await get_feature_collection("notes")
    if collection is None:
        return [note for note in _in_memory_notes if note.get("user_id") == user_id]

    try:
        return [serialize_mongo_document(doc) async for doc in collection.find({"user_id": user_id}).sort("updated_at", -1)]
    except Exception as exc:
        print(f"[MongoDB] Notes read failed: {exc}")
        return [note for note in _in_memory_notes if note.get("user_id") == user_id]


async def store_note(user_id: str, note_data: dict[str, Any]) -> dict[str, Any]:
    collection = await get_feature_collection("notes")
    document = {"user_id": user_id, **note_data}
    if collection is None:
        _in_memory_notes.append(document)
        return document

    try:
        result = await collection.insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document
    except Exception as exc:
        print(f"[MongoDB] Note save failed: {exc}")
        _in_memory_notes.append(document)
        return document


async def update_note(user_id: str, note_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    collection = await get_feature_collection("notes")
    if collection is None:
        for index, note in enumerate(_in_memory_notes):
            if note.get("user_id") == user_id and note.get("note_id") == note_id:
                _in_memory_notes[index].update(updates)
                return _in_memory_notes[index]
        return None

    try:
        result = await collection.update_one({"user_id": user_id, "note_id": note_id}, {"$set": updates})
        if result.matched_count == 0:
            return None
        return await collection.find_one({"user_id": user_id, "note_id": note_id})
    except Exception as exc:
        print(f"[MongoDB] Note update failed: {exc}")
        return None


async def delete_note(user_id: str, note_id: str) -> bool:
    collection = await get_feature_collection("notes")
    if collection is None:
        before = len(_in_memory_notes)
        _in_memory_notes[:] = [note for note in _in_memory_notes if not (note.get("user_id") == user_id and note.get("note_id") == note_id)]
        return len(_in_memory_notes) < before

    try:
        result = await collection.delete_one({"user_id": user_id, "note_id": note_id})
        return result.deleted_count > 0
    except Exception as exc:
        print(f"[MongoDB] Note delete failed: {exc}")
        return False


async def fetch_achievements(user_id: str) -> list[dict[str, Any]]:
    collection = await get_feature_collection("achievements")
    if collection is None:
        return [entry for entry in _in_memory_achievements if entry.get("user_id") == user_id]

    try:
        return [serialize_mongo_document(doc) async for doc in collection.find({"user_id": user_id}).sort("awarded_at", -1)]
    except Exception as exc:
        print(f"[MongoDB] Achievements read failed: {exc}")
        return [entry for entry in _in_memory_achievements if entry.get("user_id") == user_id]


async def store_achievement(user_id: str, achievement_data: dict[str, Any]) -> dict[str, Any]:
    collection = await get_feature_collection("achievements")
    document = {"user_id": user_id, **achievement_data}
    if collection is None:
        existing = any(item.get("user_id") == user_id and item.get("badge_id") == achievement_data.get("badge_id") for item in _in_memory_achievements)
        if existing:
            return achievement_data
        _in_memory_achievements.append(document)
        return document

    try:
        existing = await collection.find_one({"user_id": user_id, "badge_id": achievement_data.get("badge_id")})
        if existing is not None:
            return serialize_mongo_document(existing)
        result = await collection.insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document
    except Exception as exc:
        print(f"[MongoDB] Achievement save failed: {exc}")
        return document


async def store_profile_document(document: dict[str, Any]) -> dict[str, Any]:
    database = await get_database()

    if database is None:
        _in_memory_profiles.append(document)
        return document

    collection = database[MONGODB_COLLECTION_NAME]
    try:
        result = await collection.insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document
    except ServerSelectionTimeoutError as exc:
        print(f"[MongoDB] Write failed: {exc}. Falling back to in-memory storage.")
        _in_memory_profiles.append(document)
        return document

    
async def update_profile_document(user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    database = await get_database()

    if database is None:
        for index, document in enumerate(_in_memory_profiles):
            if document.get("user_id") == user_id:
                _in_memory_profiles[index].update(updates)
                return _in_memory_profiles[index]
        return None

    collection = database[MONGODB_COLLECTION_NAME]

    try:
        result = await collection.update_one(
            {"user_id": user_id},
            {"$set": updates},
        )

        if result.matched_count == 0:
            return None

        return await fetch_profile_by_user_id(user_id)

    except ServerSelectionTimeoutError as exc:
        print(f"[MongoDB] Update failed: {exc}")
        raise



async def fetch_all_profiles() -> list[dict[str, Any]]:
    collection = await get_users_collection()
    if collection is None:
        return [serialize_mongo_document(doc) for doc in _in_memory_profiles]

    try:
        documents = []
        async for doc in collection.find({}).sort("created_at", -1):
            documents.append(serialize_mongo_document(doc))
        return documents
    except ServerSelectionTimeoutError as exc:
        print(f"[MongoDB] Read failed: {exc}. Falling back to in-memory storage.")
        return [serialize_mongo_document(doc) for doc in _in_memory_profiles]


async def fetch_profile_by_user_id(user_id: str) -> dict[str, Any] | None:
    collection = await get_users_collection()
    if collection is None:
        for doc in _in_memory_profiles:
            if doc.get("user_id") == user_id:
                return serialize_mongo_document(doc)
        return None

    try:
        document = await collection.find_one({"user_id": user_id})
        return serialize_mongo_document(document)
    except ServerSelectionTimeoutError as exc:
        print(f"[MongoDB] Lookup failed: {exc}. Falling back to in-memory storage.")
        for doc in _in_memory_profiles:
            if doc.get("user_id") == user_id:
                return serialize_mongo_document(doc)
        return None


def get_in_memory_profiles() -> list[dict[str, Any]]:
    return _in_memory_profiles


async def store_test_result(
    user_id: str,
    subject: str,
    score: int,
    total_questions: int,
    percentage: int,
    review: list[dict[str, Any]],
) -> dict[str, Any]:
    from datetime import datetime, timezone

    document = {
        "user_id": user_id,
        "subject": subject,
        "score": score,
        "total_questions": total_questions,
        "percentage": percentage,
        "review": review,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    database = await get_database()
    if database is None:
        _in_memory_test_results.append(document)
        return document

    try:
        result = await database["test_results"].insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document
    except Exception as exc:
        print(f"[MongoDB] Test result save failed: {exc}")
        _in_memory_test_results.append(document)
        return document


async def fetch_test_results(user_id: str) -> list[dict[str, Any]]:
    database = await get_database()

    if database is None:
        return [
            result for result in _in_memory_test_results
            if result.get("user_id") == user_id
        ]

    try:
        collection = database["test_results"]
        cursor = collection.find(
            {"user_id": user_id},
            {"_id": 0},
        ).sort("submitted_at", 1)
        return [document async for document in cursor]
    except Exception as exc:
        print(f"[MongoDB] Test history read failed: {exc}")
        return [
            result for result in _in_memory_test_results
            if result.get("user_id") == user_id
        ]


_in_memory_chats: list[dict[str, Any]] = []


async def store_chat_message(
    user_id: str,
    message: str,
    reply: str,
) -> dict[str, Any]:
    from datetime import datetime, timezone

    document = {
        "user_id": user_id,
        "message": message,
        "reply": reply,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    database = await get_database()

    if database is None:
        _in_memory_chats.append(document)
        return document

    try:
        await database["chat_history"].insert_one(document)
        return document
    except Exception as exc:
        print(f"[MongoDB] Chat save failed: {exc}")
        raise


async def fetch_chat_history(user_id: str) -> list[dict[str, Any]]:
    database = await get_database()

    if database is None:
        return [
            chat for chat in _in_memory_chats
            if chat["user_id"] == user_id
        ]

    try:
        collection = database["chat_history"]
        cursor = collection.find(
            {"user_id": user_id},
            {"_id": 0},
        ).sort("created_at", 1)

        return [document async for document in cursor]
    except Exception as exc:
        print(f"[MongoDB] Chat history read failed: {exc}")
        raise

    
async def get_learning_plans_collection():
    database = await get_database()
    if database is None:
        return None
    return database["learning_plans"]


_in_memory_interview_sessions: list[dict[str, Any]] = []


async def store_interview_session(
    user_id: str,
    session_data: dict[str, Any],
) -> dict[str, Any]:
    from datetime import datetime, timezone

    document = {
        **session_data,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    database = await get_database()

    if database is None:
        _in_memory_interview_sessions.append(document)
        return document

    try:
        result = await database["interview_sessions"].insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document
    except Exception as exc:
        print(f"[MongoDB] Interview save failed: {exc}")
        raise


async def fetch_interview_sessions(
    user_id: str,
) -> list[dict[str, Any]]:
    database = await get_database()

    if database is None:
        return [
            session
            for session in _in_memory_interview_sessions
            if session.get("user_id") == user_id
        ]

    try:
        collection = database["interview_sessions"]
        cursor = collection.find(
            {"user_id": user_id},
            {"_id": 0},
        ).sort("created_at", -1)

        return [session async for session in cursor]
    except Exception as exc:
        print(f"[MongoDB] Interview history read failed: {exc}")
        raise

_in_memory_job_applications: list[dict[str, Any]] = []


async def store_job_application(
    user_id: str,
    application_data: dict[str, Any],
) -> dict[str, Any]:
    from datetime import datetime, timezone

    document = {
        **application_data,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    database = await get_database()

    if database is None:
        _in_memory_job_applications.append(document)
        return document

   
    result = await database["job_applications"].insert_one(document)

    document.pop("_id", None)

    return{"id": str(result.inserted_id), **document}


async def fetch_job_applications(
    user_id: str,
) -> list[dict[str, Any]]:
    database = await get_database()

    if database is None:
        return [
            application
            for application in _in_memory_job_applications
            if application.get("user_id") == user_id
        ]

    collection = database["job_applications"]
    cursor = collection.find(
        {"user_id": user_id},
        {"_id": 0},
    ).sort("created_at", -1)

    return [application async for application in cursor]


async def update_job_application_status(
    user_id: str,
    created_at: str,
    status: str,
) -> dict[str, Any] | None:
    database = await get_database()

    if database is None:
        for application in _in_memory_job_applications:
            if (
                application.get("user_id") == user_id
                and application.get("created_at") == created_at
            ):
                application["status"] = status
                return application
        return None

    collection = database["job_applications"]

    result = await collection.update_one(
        {
            "user_id": user_id,
            "created_at": created_at,
        },
        {
            "$set": {"status": status}
        },
    )

    if result.matched_count == 0:
        return None

    return await collection.find_one(
        {
            "user_id": user_id,
            "created_at": created_at,
        },
        {"_id": 0},
    )




