from sqlalchemy import (MetaData, Table, Column, String, Integer, Float, Numeric, Boolean,
                        JSON, ForeignKey, UniqueConstraint, CheckConstraint, Index)

metadata = MetaData(naming_convention={"ix": "ix_%(column_0_label)s", "uq": "uq_%(table_name)s_%(column_0_name)s",
                                      "ck": "ck_%(table_name)s_%(constraint_name)s", "pk": "pk_%(table_name)s",
                                      "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"})


def identity():
    return Column("id", String(64), primary_key=True)


def ref(name, target, **kwargs):
    return Column(name, String(64), ForeignKey(target + ".id"), nullable=False, **kwargs)


roles = Table("roles", metadata, identity(), Column("name", String(20), unique=True, nullable=False))
llm_daily_usage = Table("llm_daily_usage", metadata,
    Column("day", Integer, primary_key=True), Column("subject", String(64), primary_key=True),
    Column("attempts", Integer, nullable=False, default=0))
users = Table("users", metadata, identity(), Column("email", String(120), unique=True, nullable=False),
              Column("password_hash", String(256), nullable=False), ref("role_id", "roles"),
              Column("disabled", Boolean, nullable=False, default=False))
suppliers = Table("suppliers", metadata, identity(), Column("name", String(80), nullable=False))
locations = Table("locations", metadata, identity(), Column("name", String(80), nullable=False))
parts = Table("parts", metadata, identity(), Column("description", String(240), nullable=False),
              ref("supplier_id", "suppliers"), Column("category", String(30), nullable=False),
              Column("unit_cost", Numeric(14, 2), nullable=False), Column("criticality", Integer, nullable=False),
              Column("synthetic", Boolean, nullable=False, default=True),
              CheckConstraint("unit_cost >= 0", name="positive_cost"), CheckConstraint("criticality BETWEEN 1 AND 3", name="criticality"))
demand_history = Table("demand_history", metadata, ref("part_id", "parts", primary_key=True),
                       ref("location_id", "locations", primary_key=True), Column("period", String(7), primary_key=True),
                       Column("qty", Float, nullable=False), CheckConstraint("qty >= 0", name="qty"))
Index("ix_demand_period", demand_history.c.period, demand_history.c.part_id, demand_history.c.location_id)
lead_time_params = Table("lead_time_params", metadata, ref("part_id", "parts", primary_key=True),
                         Column("mean_months", Float, nullable=False), Column("std_months", Float, nullable=False))
cost_params = Table("cost_params", metadata, ref("part_id", "parts", primary_key=True),
                    Column("holding_rate", Float, nullable=False), Column("stockout_penalty", Float, nullable=False),
                    Column("expedite_cost", Float, nullable=False), Column("synthetic", Boolean, nullable=False))
product_models = Table("product_models", metadata, identity(), Column("name", String(80), nullable=False))
option_groups = Table("option_groups", metadata, identity(), ref("model_id", "product_models"),
                      Column("minimum", Integer, nullable=False), Column("maximum", Integer, nullable=False))
options = Table("options", metadata, identity(), ref("group_id", "option_groups"), Column("name", String(80), nullable=False))
compatibility_rules = Table("compatibility_rules", metadata, identity(), ref("option_id", "options"),
                            ref("other_option_id", "options"), Column("kind", String(20), nullable=False))
product_configs = Table("product_configs", metadata, identity(), ref("model_id", "product_models"),
                        Column("option_ids", JSON, nullable=False))
config_bom = Table("config_bom", metadata, identity(), ref("model_id", "product_models"), ref("part_id", "parts"),
                   Column("option_id", String(64), ForeignKey("options.id")), Column("qty", Integer, nullable=False),
                   CheckConstraint("qty > 0", name="quantity"))
purchase_orders = Table("purchase_orders", metadata, identity(), ref("part_id", "parts"),
                        Column("period", String(7), nullable=False), Column("qty", Integer, nullable=False),
                        Column("standard_price", Numeric(14, 2), nullable=False), Column("actual_price", Numeric(14, 2), nullable=False),
                        Column("budget", Numeric(14, 2), nullable=False), Column("expedite_spend", Numeric(14, 2), nullable=False))
staging_extracts = Table("staging_extracts", metadata, identity(), Column("sap_table", String(20), nullable=False),
                        Column("payload", JSON, nullable=False), Column("label", String(100), nullable=False))
data_quality_issues = Table("data_quality_issues", metadata, identity(), Column("run_id", String(64), nullable=False, index=True),
                           Column("rule", String(40), nullable=False), Column("row_data", JSON, nullable=False),
                           Column("quarantined", Boolean, nullable=False), Column("created_at", Float, nullable=False))
jobs = Table("jobs", metadata, identity(), Column("owner", String(120), nullable=False), Column("kind", String(30), nullable=False),
             Column("idempotency_key", String(100), nullable=False), Column("payload", JSON, nullable=False),
             Column("status", String(20), nullable=False, index=True), Column("progress", Integer, nullable=False, default=0),
             Column("attempts", Integer, nullable=False, default=0), Column("available_at", Float, nullable=False),
             Column("lease_until", Float), Column("lease_token", String(64)), Column("result", JSON),
             Column("error", String(80)), Column("created_at", Float, nullable=False), Column("updated_at", Float, nullable=False),
             UniqueConstraint("owner", "idempotency_key"), CheckConstraint("progress BETWEEN 0 AND 100", name="progress"))
refresh_tokens = Table("refresh_tokens", metadata, identity(), Column("family", String(64), nullable=False, index=True),
                       Column("username", String(120), nullable=False), Column("expires_at", Float, nullable=False),
                       Column("used", Boolean, nullable=False), Column("revoked", Boolean, nullable=False))
assistant_sessions = Table("assistant_sessions", metadata, identity(), Column("owner", String(120), nullable=False))
tool_call_log = Table("tool_call_log", metadata, identity(), ref("session_id", "assistant_sessions"),
                      Column("owner", String(120), nullable=False), Column("tool", String(50), nullable=False),
                      Column("args", JSON, nullable=False), Column("status", String(20), nullable=False),
                      Column("latency_ms", Float, nullable=False), Column("created_at", Float, nullable=False))
audit_log = Table("audit_log", metadata, identity(), Column("actor", String(120), nullable=False),
                  Column("action", String(60), nullable=False), Column("detail", JSON, nullable=False),
                  Column("created_at", Float, nullable=False, index=True))
idempotency_keys = Table("idempotency_keys", metadata, identity(), Column("owner", String(120), nullable=False),
                         ref("job_id", "jobs"), Column("created_at", Float, nullable=False))
artifacts = {}
for name in ("forecast_runs", "forecasts", "policies", "simulation_runs", "recommendations", "kpi_snapshots", "dq_runs"):
    artifacts[name] = Table(name, metadata, identity(), Column("part_id", String(64), ForeignKey("parts.id")),
                            Column("run_id", String(64), nullable=False, index=True),
                            Column("payload", JSON, nullable=False), Column("created_at", Float, nullable=False, index=True))
results = Table("results", metadata, identity(), Column("payload", JSON, nullable=False),
                Column("created_at", Float, nullable=False))
login_attempts = Table("login_attempts", metadata, identity(), Column("failures", Integer, nullable=False),
                       Column("locked_until", Float, nullable=False))
warehouse_inventory = Table("warehouse_inventory", metadata, ref("part_id", "parts", primary_key=True),
                            ref("location_id", "locations", primary_key=True), Column("quantity", Float, nullable=False),
                            Column("standard_price", Numeric(14, 2), nullable=False), Column("lead_days", Float, nullable=False))
warehouse_sales = Table("warehouse_sales", metadata, identity(), ref("part_id", "parts"),
                        ref("location_id", "locations"), Column("period", String(7), nullable=False),
                        Column("quantity", Float, nullable=False))
