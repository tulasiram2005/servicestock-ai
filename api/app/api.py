from typing import Literal
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update

from .db import schema as db
from . import services


class WhatIf(BaseModel):
    model_config = ConfigDict(extra="forbid")
    part_id: str | None = Field(default=None, max_length=64, pattern=r"^P[0-9]{4}$")
    service_level: float = Field(default=0.95, ge=0.8, le=0.999)
    holding_cost_rate: float = Field(default=0.2, ge=0.01, le=1)
    lead_time_multiplier: float = Field(default=1, ge=0.5, le=3)
    idempotency_key: str = Field(min_length=8, max_length=100)


class RoleChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["viewer", "planner", "admin"]
    disabled: bool = False


class Configuration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_id: str = Field(max_length=64)
    options: list[str] = Field(max_length=20)


def router(store, settings, authorize, admin, queue, wake, cache):
    route = APIRouter(prefix="/api")

    def database():
        if store is None:
            raise HTTPException(503, "Database is not configured")
        return store

    def planner(principal=Depends(authorize)):
        if principal.role not in {"planner", "admin"}:
            raise HTTPException(403, "Planner access required")
        return principal

    @route.get("/configurations")
    def configurations(principal=Depends(authorize), database=Depends(database)):
        from .configurations import catalog, pooling
        return {**catalog(database), "pooling": pooling(database)}

    @route.post("/configurations/evaluate")
    def evaluate_configuration(body: Configuration, principal=Depends(authorize), database=Depends(database)):
        from .configurations import evaluate
        return evaluate(database, body.model_id, body.options)

    @route.get("/parts")
    def parts(query: str = Query(default="", max_length=80), cursor: str = Query(default="", max_length=64),
              limit: int = Query(default=20, ge=1, le=100), principal=Depends(authorize), database=Depends(database)):
        with database.transaction() as connection:
            statement = select(db.parts).where(db.parts.c.id > cursor)
            if query:
                statement = statement.where(db.parts.c.description.contains(query, autoescape=True) | db.parts.c.id.contains(query, autoescape=True))
            rows = connection.execute(statement.order_by(db.parts.c.id).limit(limit + 1)).mappings().all()
        return {"items": [dict(row) for row in rows[:limit]], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @route.get("/parts/{part_id}")
    def part(part_id: str, principal=Depends(authorize), database=Depends(database)):
        return services.part_detail(database, part_id)

    @route.get("/kpis")
    def kpis(principal=Depends(authorize), database=Depends(database)):
        cached = cache.get("kpis")
        if cached is None:
            data = services.artifact(database, "analytics")
            cached = {"kpis": data["kpis"], "finance": data["finance"], "source_id": "analytics",
                      "synthetic_cost_assumptions": True}
            cache.put("kpis", cached)
        return cached

    @route.get("/dq")
    def quality(principal=Depends(authorize), database=Depends(database)):
        with database.transaction() as connection:
            return connection.scalar(select(db.artifacts["dq_runs"].c.payload).order_by(db.artifacts["dq_runs"].c.created_at.desc()).limit(1))

    @route.get("/results")
    def results(principal=Depends(authorize), database=Depends(database)):
        with database.transaction() as connection:
            return {row.id: row.payload for row in connection.execute(select(db.results))}

    @route.post("/whatif")
    def what_if(body: WhatIf, principal=Depends(planner), database=Depends(database)):
        payload = body.model_dump(exclude={"idempotency_key"})
        job = queue.enqueue(principal.username, "whatif", payload, body.idempotency_key)
        database.audit(principal.username, "enqueue_whatif", {"job_id": job["id"]})
        wake()
        return {"job_id": job["id"], "status": job["status"]}

    @route.get("/whatif")
    def preview(part_id: str | None = None, service_level: float = Query(0.95, ge=0.8, le=0.999),
                holding_cost_rate: float = Query(0.2, ge=0.01, le=1), lead_time_multiplier: float = Query(1, ge=0.5, le=3),
                principal=Depends(authorize), database=Depends(database)):
        return services.whatif(database, {"part_id": part_id, "service_level": service_level,
                               "holding_cost_rate": holding_cost_rate, "lead_time_multiplier": lead_time_multiplier})

    @route.get("/jobs/{job_id}")
    def job_status(job_id: str, principal=Depends(authorize), database=Depends(database)):
        wake()
        with database.transaction() as connection:
            row = connection.execute(select(db.jobs).where(db.jobs.c.id == job_id)).mappings().first()
        if not row or (principal.role != "admin" and row["owner"] != principal.username):
            raise HTTPException(404, "Job not found")
        return {key: row[key] for key in ("id", "status", "progress", "attempts", "result", "error")}

    @route.get("/admin/usage", dependencies=[Depends(admin)])
    def budget(database=Depends(database)):
        return services.usage(database, settings)

    @route.post("/admin/retention", dependencies=[Depends(admin)])
    def retention(database=Depends(database)):
        job = queue.enqueue(settings.admin_username, "retention", {}, uuid.uuid4().hex)
        wake()
        return {"job_id": job["id"]}

    @route.get("/admin/audit", dependencies=[Depends(admin)])
    def audit(database=Depends(database)):
        with database.transaction() as connection:
            return [dict(row) for row in connection.execute(select(db.audit_log).order_by(db.audit_log.c.created_at.desc()).limit(100)).mappings()]

    @route.get("/admin/users", dependencies=[Depends(admin)])
    def users(database=Depends(database)):
        with database.transaction() as connection:
            return [dict(row) for row in connection.execute(select(db.users.c.id, db.users.c.email, db.users.c.role_id, db.users.c.disabled)).mappings()]

    @route.post("/admin/users/{user_id}")
    def change_role(user_id: str, body: RoleChange, principal=Depends(admin), database=Depends(database)):
        with database.transaction() as connection:
            row = connection.execute(select(db.users).where(db.users.c.id == user_id)).mappings().first()
            if not row:
                raise HTTPException(404, "User not found")
            if row["email"] in {settings.admin_username, settings.demo_username}:
                raise HTTPException(403, "Environment-managed accounts cannot be modified")
            connection.execute(update(db.users).where(db.users.c.id == user_id).values(role_id=body.role, disabled=body.disabled))
        database.audit(principal.username, "change_role", {"user_id": user_id, **body.model_dump()})
        return {"status": "updated"}

    return route
