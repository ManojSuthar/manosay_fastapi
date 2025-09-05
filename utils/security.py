# utils/security.py
import asyncio
import bcrypt
from typing import Callable, Any


def _run_in_executor(func: Callable[..., Any], *args) -> Any:
    """
    Helper to run blocking function in default ThreadPoolExecutor.
    Returns the result (to be awaited).
    """
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, func, *args)


async def hash_password(password: str) -> str:
    def _hash(pw: bytes) -> bytes:
        return bcrypt.hashpw(pw, bcrypt.gensalt())
    hashed = await _run_in_executor(_hash, password.encode("utf-8"))
    return hashed.decode("utf-8")


async def verify_password(password: str, hashed: str) -> bool:
    def _check(pw: bytes, h: bytes) -> bool:
        try:
            return bcrypt.checkpw(pw, h)
        except Exception:
            return False
    return await _run_in_executor(_check, password.encode("utf-8"), hashed.encode("utf-8"))
