from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dataclasses import dataclass, field as dc_field
from typing import List, Dict, Optional

app = FastAPI(title="DevOps Monitoring API", version="1.0")


# ─── Internal model ─────────────────────────────────────────────────────────

@dataclass
class Server:
    id: int
    name: str
    host: str
    port: int
    status: str = "unknown"
    tags: List[str] = dc_field(default_factory=list)

    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


# ─── Pydantic schemas ────────────────────────────────────────────────────────

class ServerIn(BaseModel):
    name: str
    host: str
    port: int = Field(default=8080, ge=1, le=65535)
    tags: List[str] = []


class ServerOut(BaseModel):
    id: int
    name: str
    host: str
    port: int
    status: str
    tags: List[str] = []

    model_config = {"from_attributes": True}



# ─── In-memory store ─────────────────────────────────────────────────────────

_store: Dict[int, Server] = {}
_counter = 0


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "DevOps Monitoring API",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health():
    return {"status": "ok", "servers": len(_store)}


@app.post("/servers", response_model=ServerOut, status_code=201)
async def register_server(server: ServerIn):
    global _counter
    _counter += 1

    record = Server(
        id=_counter,
        name=server.name,
        host=server.host,
        port=server.port,
        tags=server.tags,
    )
    _store[_counter] = record
    return record

@app.get("/servers", response_model=List[ServerOut])
async def list_servers(status: Optional[str] = None):
    if status is None:
        return list(_store.values())

    return [
        server
        for server in _store.values()
        if server.status.lower() == status.lower()
    ]


@app.get("/servers/{server_id}", response_model=ServerOut)
async def get_server(server_id: int):
    server = _store.get(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


@app.delete("/servers/{server_id}", status_code=204)
async def delete_server(server_id: int):
    if server_id not in _store:
        raise HTTPException(status_code=404, detail="Server not found")
    del _store[server_id]


@app.post("/servers/{server_id}/check", response_model=ServerOut)
async def trigger_check(server_id: int):
    import httpx

    if server_id not in _store:
        raise HTTPException(status_code=404, detail="Server not found")

    server = _store[server_id]

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{server.base_url()}/health")
            server.status = "UP" if resp.status_code == 200 else "DEGRADED"
    except Exception:
        server.status = "DOWN"

    return server