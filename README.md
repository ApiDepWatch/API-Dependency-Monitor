# API Dependency Monitor

A GitHub Action that monitors your workflow's outbound HTTP traffic and validates it against an OpenAPI specification. It tells you whether your application is making API calls that match your spec — catching breaking changes and undocumented usage before they reach production.

---

## How it works

1. A mitmproxy-based HTTP proxy starts in the background at the beginning of your job
2. All outbound HTTP/HTTPS traffic from subsequent steps is automatically routed through the proxy
3. Each intercepted request is sent to a validation backend, which checks it against your OpenAPI spec
4. At the end of your job, the stop action shuts down the proxy and prints a summary of every request — passed or failed
5. The job exits with a non-zero code if any requests failed validation

---

## Setup

### Repository variables

Set the following in your repository's **Settings → Secrets and variables → Actions → Variables**:

| Variable | Description |
|---|---|
| `BACKEND_URL` | Base URL of the API management backend (e.g. `https://your-backend.com`) |
| `PATH_TO_API_SPEC` | Path or URL to your OpenAPI spec file |

---

## Usage

Add the two actions to your workflow — one to start the proxy, one to stop it.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Start the proxy
      - uses: BuildMore-io/API-Dependency-Monitor@main
        with:
          backend_url: ${{ vars.BACKEND_URL }}
          path_to_api_spec: ${{ vars.PATH_TO_API_SPEC }}
          host_name: api.example.com   # optional: filter to a specific host

      # Your steps here — all HTTP traffic is automatically intercepted
      - name: Run tests
        run: npm test

      # Stop the proxy and report results
      - uses: BuildMore-io/API-Dependency-Monitor/stop_proxy@main
        if: always()
```

The `if: always()` on the stop step ensures the proxy is shut down and results are printed even if an earlier step fails.

---

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `backend_url` | No | `''` | Base URL of the validation backend |
| `path_to_api_spec` | No | `''` | Path to the OpenAPI spec file |
| `host_name` | No | `''` | Hostname to monitor (e.g. `api.example.com`) |

---

## Output

When the stop action runs, it prints a JSON summary to the Actions log:

```json
{
  "captured": 5,
  "passed": 4,
  "failed": 1
}
```

Each individual request is also logged with a pass/fail indicator:

- `✅` — request matches the OpenAPI spec
- `❌` — request violates the spec
- `⚠️` — request could not be validated (e.g. network error reaching the backend)

If any requests failed validation, the summary is emitted as a GitHub Actions `::warning::` annotation and the job exits with code `1`.

---

## How the proxy intercepts traffic

When the start action runs, it sets `HTTP_PROXY` and `HTTPS_PROXY` environment variables pointing to `http://localhost:8080`. Most HTTP clients (curl, Python requests, npm, etc.) automatically respect these variables, so no changes to your application code are needed.

The mitmproxy CA certificate is also installed into the system trust store so HTTPS traffic can be intercepted without TLS errors.
