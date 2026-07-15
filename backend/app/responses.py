from typing import Any


def ok(data: Any = None, message: str | None = None) -> dict[str, Any]:
    return {"success": True, "data": data, "message": message}


def fail(message: str, data: Any = None) -> dict[str, Any]:
    return {"success": False, "data": data, "message": message}
