import logging
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException

from models import Server, ServerIn, ServerOut
from health import HealthChecker


# ─────────────────────────────────────────────────────────────
# Configuration logging
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────

app = FastAPI(title="DevOps Monitoring API", version="1.0")


# ─────────────────────────────────────────────────────────────
# In-memory store
# ─────────────────────────────────────────────────────────────

_store: Dict[int, Server] = {}
_counter = 0
checker = HealthChecker()


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """API health check."""
    return {
        "status": "ok",
        "servers_monitored": len(_store),
    }


@app.post("/servers", response_model=ServerOut, status_code=201)
async def register_server(server: ServerIn):
    """Register a new server."""
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
    logger.info("Registered server %s (%s:%s)", record.name, record.host, record.port)
    return record


@app.get("/servers", response_model=List[ServerOut])
async def list_servers(status: Optional[str] = None):
    """List all servers, optionally filtered by status."""
    servers = list(_store.values())

    if status:
        servers = [s for s in servers if s.status == status]

    return servers


@app.get("/servers/{server_id}", response_model=ServerOut)
async def get_server(server_id: int):
    """Get one server by ID."""
    if server_id not in _store:
        raise HTTPException(status_code=404, detail="Server not found")

    return _store[server_id]


@app.delete("/servers/{server_id}", status_code=204)
async def delete_server(server_id: int):
    """Delete a server."""
    if server_id not in _store:
        raise HTTPException(status_code=404, detail="Server not found")

    deleted = _store.pop(server_id)
    logger.info("Deleted server %s", deleted.name)


@app.post("/servers/{server_id}/check", response_model=ServerOut)
async def trigger_health_check(server_id: int):
    """Trigger a health check on a server."""
    if server_id not in _store:
        raise HTTPException(status_code=404, detail="Server not found")

    server = _store[server_id]
    await checker.check(server)

    return server
