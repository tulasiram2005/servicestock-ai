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

## Follow-up 2026-10-29 09:59 UTC

Ollama's local model metadata advertises `completion` and `tools`. An explicit
local warm-up completed, but the subsequent application-native request still
fell back after 5.026 seconds with no validated tools. Warm-up did not resolve
the runtime limit. Advertised support is not a successful application validation.
No remote request, new model download, or timeout increase was used.
