import asyncio
import hashlib
import time
from collections import defaultdict, deque
from fastapi import APIRouter, File, Header, HTTPException, Request, UploadFile
from stego_svc import formats
from stego_svc.verdict import classify

router = APIRouter()
_events = []
_requests = defaultdict(deque)

@router.post("/api/steganography/analyze")
@router.post("/api/stego/analyze")
async def analyze(request: Request, file: UploadFile = File(...), x_user_id: str | None = Header(None), x_user_perms: str = Header(""), x_service_name: str | None = Header(None), x_service_token: str | None = Header(None)):
    caller = getattr(request.state, "caller", None)
    if not x_user_id or caller != "gateway":
        _events.append({"event": "perm.denied", "user_id": x_user_id}); raise HTTPException(401, "identidad no válida")
    if "steganography.analyze" not in {p.strip() for p in x_user_perms.split(",")}:
        _events.append({"event": "perm.denied", "user_id": x_user_id}); raise HTTPException(403, "permiso insuficiente")
    now = time.monotonic(); bucket = _requests[x_user_id]
    while bucket and now - bucket[0] >= 60: bucket.popleft()
    settings = getattr(request.app.state, "settings", None)
    per_min = getattr(settings, "analyze_per_min", 10)
    max_bytes = getattr(settings, "upload_max_bytes", 5 * 1024 * 1024)
    max_pixels = getattr(settings, "max_image_pixels", 20_000_000)
    timeout = getattr(settings, "stego_timeout_s", 10.0)
    if len(bucket) >= per_min:
        _events.append({"event": "stego.ratelimited", "user_id": x_user_id}); raise HTTPException(429, "límite de análisis excedido")
    bucket.append(now)
    data = await file.read(max_bytes + 1)
    kind, reasons = formats.validate(data, max_bytes=max_bytes, max_pixels=max_pixels)
    if not kind: raise HTTPException(422, {"error": "archivo no permitido", "motivos": reasons})
    try:
        result = await asyncio.wait_for(asyncio.to_thread(formats.FORMATS[kind].analyze, data, {"chi2_p": .995, "rs_rate": .15, "entropy_trigger": None, "max_pixels": max_pixels}), timeout=timeout)
    except asyncio.TimeoutError:
        result = {"suspicious": True, "reasons": ["análisis excedió el tiempo límite"], "metrics": {}}
    response = {"verdict": classify(result), "mime": kind, "sha256": hashlib.sha256(data).hexdigest(), "motivos": result["reasons"], "checks": result["metrics"]}
    _events.append({"event": "stego.analyzed", "user_id": x_user_id, "verdict": response["verdict"]})
    return response
