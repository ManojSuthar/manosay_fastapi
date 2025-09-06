# db.py
from __future__ import annotations
import os
import asyncio
import logging
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

load_dotenv()
logger = logging.getLogger(__name__)

# Globals (module-level singletons per process)
_client: Optional[AsyncIOMotorClient] = None
_database = None

# Read env (these should exist in your .env as you provided)
MONGO_URI: Optional[str] = os.getenv("MONGO_URI")
MONGO_DB: Optional[str] = os.getenv("MONGO_DB")

# Basic validation
if not MONGO_URI or not MONGO_DB:
    raise RuntimeError(
        "MONGO_URI and MONGO_DB must be set in environment / .env")

# Default connection tuning
_DEFAULT_SERVER_SELECTION_TIMEOUT_MS = 5000
_DEFAULT_CONNECT_RETRIES = 3
_DEFAULT_RETRY_BACKOFF_SECONDS = 1.0  # will exponentiate


async def connect_to_mongo(
    *,
    server_selection_timeout_ms: int = _DEFAULT_SERVER_SELECTION_TIMEOUT_MS,
    max_retries: int = _DEFAULT_CONNECT_RETRIES,
    base_backoff: float = _DEFAULT_RETRY_BACKOFF_SECONDS,
) -> None:

    global _client, _database

    if _client is not None:
        # already connected
        return

    last_exc: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            _client = AsyncIOMotorClient(
                MONGO_URI,
                serverSelectionTimeoutMS=server_selection_timeout_ms,
            )
            _database = _client[MONGO_DB]
            # Ping to ensure connectivity
            await _client.admin.command("ping")
            logger.info("Connected to MongoDB (uri=%s, db=%s)",
                        _safe_uri_display(MONGO_URI), MONGO_DB)
            return
        except Exception as exc:  # broad because Motor/PyMongo can raise different errors
            last_exc = exc
            logger.warning(
                "MongoDB connect attempt %d/%d failed: %s",
                attempt,
                max_retries,
                exc,
            )
            # close any partially-created client
            try:
                if _client:
                    _client.close()
            except Exception:
                logger.exception(
                    "Error closing partial MongoDB client after failed attempt")
            _client = None
            _database = None

            if attempt < max_retries:
                backoff = base_backoff * (2 ** (attempt - 1))
                logger.info("Retrying MongoDB connect in %.2fs...", backoff)
                await asyncio.sleep(backoff)

    # If we exit loop, all retries failed
    logger.exception("All MongoDB connection attempts failed")
    raise RuntimeError(
        f"Could not connect to MongoDB after {max_retries} attempts") from last_exc


def close_mongo_connection() -> None:
    global _client, _database
    if _client:
        try:
            _client.close()
            logger.info("Closed MongoDB connection")
        except Exception:
            logger.exception("Error while closing MongoDB connection")
    _client = None
    _database = None


def get_client() -> AsyncIOMotorClient:
    if _client is None:
        raise RuntimeError(
            "MongoDB client is not initialized. Call connect_to_mongo() in startup.")
    return _client


def get_database():
    if _database is None:
        raise RuntimeError(
            "MongoDB database is not initialized. Call connect_to_mongo() in startup.")
    return _database


async def ensure_indexes() -> None:
    db = get_database()
    try:
        # Ensure unique user email
        await db["users"].create_index("email", unique=True)
        logger.info("Ensured index: users.email (unique)")

        # Ensure unique slug for posts (so two posts can't share same slug)
        # NOTE: this will fail if duplicate slugs already exist in the collection.
        await db["posts"].create_index("slug", unique=True)
        logger.info("Ensured index: posts.slug (unique)")
    except PyMongoError:
        logger.exception("Failed to ensure indexes on startup")


async def ping_db() -> bool:
    try:
        client = get_client()
        await client.admin.command("ping")
        return True
    except Exception:
        logger.exception("DB ping failed")
        return False


def connection_info() -> Dict[str, Any]:
    return {
        "uri": _safe_uri_display(MONGO_URI),
        "db": MONGO_DB,
        "connected": _client is not None,
    }


def _safe_uri_display(uri: Optional[str]) -> str:
    if not uri:
        return "<missing>"
    try:
        if "@" in uri:
            parts = uri.split("@", 1)
            creds, rest = parts[0], parts[1]
            if "://" in creds:
                scheme, _ = creds.split("://", 1)
                return f"{scheme}://<redacted>@{rest}"
        return uri
    except Exception:
        return "<invalid-uri>"
