# Local native-model validation — 2026-10-29

Installed model: mistral:latest (4.4 GB). Two actual native routing attempts were
made using the application router and its five-second HTTP timeout. Both fell
back without validated tools after approximately five seconds. No external model
calls, keys or paid services were used; no models were downloaded.

This verifies safe fallback with this local setup, not successful native-tool
support. Simulated native response tests pass, but live successful capability
remains unverified. The five-second limit was retained; do not silently relax
production request limits to obtain a passing result.

The latest machine-readable attempt is results/local_native_model.json.
