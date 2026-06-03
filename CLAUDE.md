# API Dependency Monitor

A GitHub Action (composite) that runs a mitmproxy-based HTTP proxy to intercept and validate API traffic against an OpenAPI specification. Intended to be published to the GitHub Actions Marketplace.

## What it does

When added to a workflow, the action:
1. Starts an HTTP proxy (mitmproxy) on a configurable port
2. All HTTP traffic routed through the proxy is intercepted and sent to a backend validation service (`BACKEND_URL/IsRequestValid`) which checks the request against an OpenAPI spec
3. On shutdown, prints a JSON summary of captured requests and pass/fail results

## Project structure

```
/
├── action.yml                        # GitHub Action definition (composite)
├── api-dep-moniter.py                # Entrypoint: starts mitmproxy via asyncio
├── moniter.py                        # mitmproxy addon: APIDependencyMonitor class + output logic
├── requirments.txt                   # pip dependencies (note: intentional typo in filename)
├── .env                              # Local env vars (not committed)
├── test/
│   └── testing_github_action.py     # pytest unit tests
└── .github/
    └── workflows/
        └── test.yml                  # Workflow to test the action itself
```

## Key files

### `moniter.py`
Contains the core logic:
- `APIDependencyMonitor` — mitmproxy addon class. Registered via `mitmproxy_engine.addons.add(...)`. mitmproxy automatically calls its hooks:
  - `request(flow)` — called on every intercepted HTTP request; formats it as raw HTTP and calls `_validate_request_against_openapi_spec`
- `_validate_request_against_openapi_spec(raw_http_request)` — POSTs the raw HTTP to `BACKEND_URL/IsRequestValid` and appends the result to `self.results`. Appends an error string on network failure.
- `output_results()` — prints a JSON summary of captured and validated requests (called by the SIGINT handler in `api-dep-moniter.py`)

**Note:** The validation call is live and hits the real backend. One commented-out line (`response.text`) was replaced with `response` (the object) — this is a minor in-progress change and causes result strings to show the response object repr rather than the body text.

### `api-dep-moniter.py`
Entrypoint script. Reads config from environment variables (`PORT`, `ORG_ID`, `PROJECT_NAME`), creates a mitmproxy `DumpMaster`, registers `APIDependencyMonitor` as an addon, and runs the event loop.

Additional responsibilities:
- Writes its PID to `moniter_pid.txt` so the workflow can send signals to it
- Registers a `SIGINT` handler that calls `traffic_monitor.output_results()`, calculates an exit code (0 if all results contain `✅`, else 1), writes the exit code to `exit_code.txt`, and calls `sys.exit()`

### `action.yml`
Composite action definition. Steps:
1. `actions/setup-python@v5` — installs Python
2. `pip install -r requirments.txt` — installs dependencies
3. `python api-dep-moniter.py > /tmp/proxy.log 2>&1 &` — starts proxy in background, output to `/tmp/proxy.log`
4. `sleep 5` — waits for mitmproxy to finish binding to the port
5. Installs the mitmproxy CA certificate into the system trust store (`/usr/local/share/ca-certificates/`) so HTTPS traffic can be intercepted without TLS errors
6. Sets `HTTP_PROXY` and `HTTPS_PROXY` env vars to `http://localhost:<port>` so subsequent workflow steps automatically route traffic through the proxy

Inputs: `port` (default `8080`), `org_id` (default `123`), `project_name` (default `TestProject`)

### `.github/workflows/test.yml`
Tests the action end-to-end:
1. Calls `uses: ./` to start the proxy
2. Sends 5 curl requests to `httpbin.org` — 4 through the proxy (`-x http://localhost:8080`) and 1 directly (to verify non-proxied traffic is unaffected)
3. Checks that the proxy process (identified by PID from `moniter_pid.txt`) is still alive
4. Stops the proxy by sending `kill -SIGINT $PID`; waits up to 60s for it to exit, then falls back to SIGKILL
5. Prints `/tmp/proxy.log` to surface proxy output in the Actions log
6. Reads `exit_code.txt` (written by the SIGINT handler) and exits with that code to fail the job on validation errors
7. Checks that the proxy process is now dead

Triggers: `push`, `pull_request`, `workflow_dispatch`

## Environment variables

| Variable | Where set | Purpose |
|---|---|---|
| `BACKEND_URL` | `.env` / CI secret | Base URL of the API management backend |
| `PORT` | `action.yml` inputs | Port for the proxy to listen on |
| `ORG_ID` | `action.yml` inputs | Organization ID for validation API |
| `PROJECT_NAME` | `action.yml` inputs | Project name for validation API |

## Running tests

```
pytest test/testing_github_action.py -v
```

## Local development with act

```
act push
```

Requires Docker Desktop running. Uses `catthehacker/ubuntu:act-latest` (set in `C:\Users\user\AppData\Local\act\actrc`).

**Known limitation:** `act` runs each workflow step as a separate `docker exec`, which can cause background processes started with `&` to not survive between steps. This works correctly on real GitHub Actions runners.

## Dependencies

- `mitmproxy` — HTTP proxy engine
- `requests` — HTTP client for calling the validation backend
- `python-dotenv` — loads `.env` for local development
- `pytest` + `responses` — unit testing and HTTP mock
