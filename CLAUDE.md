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
  - `request(flow)` — called on every intercepted HTTP request; formats it as raw HTTP and validates it
  - `done()` — called by mitmproxy at shutdown; prints the JSON results summary
- `output_results_and_exit(traffic_monitor)` — standalone function used in unit tests to assert exit codes

**Note:** The real HTTP validation call (`http_requests.post(BACKEND_URL/IsRequestValid, ...)`) is currently stubbed out with a hardcoded `"✅ Request matches spec."` response for development/testing. The real call is commented out and can be restored.

### `api-dep-moniter.py`
Entrypoint script. Reads config from environment variables (`PORT`, `ORG_ID`, `PROJECT_NAME`), creates a mitmproxy `DumpMaster`, registers `APIDependencyMonitor` as an addon, and runs the event loop.

### `action.yml`
Composite action definition. Steps:
1. `actions/setup-python@v5` — installs Python
2. `pip install -r requirments.txt` — installs dependencies
3. `python api-dep-moniter.py > /tmp/proxy.log 2>&1 &` — starts proxy in background, output to `/tmp/proxy.log`
4. `sleep 5` — waits for mitmproxy to finish binding to the port

Inputs: `port` (default `8080`), `org_id`, `project_name`

### `.github/workflows/test.yml`
Tests the action end-to-end:
1. Calls `uses: ./` to start the proxy
2. Sends 4 curl requests through the proxy to `httpbin.org`
3. Stops the proxy with `pkill -SIGINT` (SIGINT triggers the mitmproxy shutdown lifecycle which calls `done()`)
4. Reads and prints `/tmp/proxy.log` to surface results in the Actions log

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
