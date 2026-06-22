# API Dependency Monitor

A GitHub Action that sits inside your CI pipeline and monitors every outbound HTTP and HTTPS request your workflow makes — validating each one against its appropriate OpenAPI specification in real time.

This is a **self-hosted** solution. There is no hosted service to sign up for. You run your own instance of the backend, you own your data, and you register whichever OpenAPI specs you want to monitor. The **[API Dependency Management Platform Backend](https://github.com/talK951/API-Dependency-Management-Platform-Backend)** is a separate open-source project you deploy yourself — this action is the GitHub Actions integration that talks to it.

Once your backend is running, this action intercepts every outbound request in your workflow and sends it to your backend for validation. The backend looks up the appropriate OpenAPI spec for the target API and checks whether the request is valid against it. If not, the action flags it and fails the job.

This means it is not limited to APIs you own or build. As long as a spec is registered on your platform instance, any request your workflow makes to that API will be validated. If your application calls a third-party API — a payment provider, a data service, an internal platform — and that spec is registered, this action will catch any requests that violate it.

This catches things like:
- Calls to endpoints that have been removed or renamed
- Requests with missing or incorrect parameters
- Payloads that don't match the expected schema
- Usage of an API your application was never supposed to call

All without changing a single line of your application code.

---

## How it works

1. At the start of your job, a mitmproxy-based HTTP proxy is launched in the background
2. The action configures the environment so that all outbound HTTP and HTTPS traffic from subsequent steps flows through the proxy automatically
3. Every intercepted request is forwarded to your self-hosted backend, which identifies the target API, looks up its registered OpenAPI spec, and validates the request against it
4. When your job finishes, a second action shuts the proxy down and prints a full summary of every request — which passed, which failed, and why
5. If any request failed validation, the job exits with a non-zero code so your pipeline fails visibly

---

## Prerequisites

This action requires a running instance of the **[API Dependency Management Platform Backend](https://github.com/talK951/API-Dependency-Management-Platform-Backend)**. You host it yourself — visit that repository for full instructions on how to deploy it.

Once your backend is up and running you will have:
- A `BACKEND_URL` — the URL of your deployed backend instance
- A platform where you can register OpenAPI specs for any APIs you want to monitor

---

## Setup

### Step 1 — Deploy the backend

Follow the instructions in the **[API Dependency Management Platform Backend](https://github.com/talK951/API-Dependency-Management-Platform-Backend)** repository to get your own instance running. Register the OpenAPI specs for the APIs you want to monitor.

### Step 2 — Add your backend URL as a repository variable

In the repository where you want to use this action, go to:

**Settings → Secrets and variables → Actions → Variables → New repository variable**

Add the following:

| Name | Value |
|---|---|
| `BACKEND_URL` | The URL of your self-hosted backend (e.g. `https://your-backend.example.com`) |
| `PATH_TO_API_SPEC` | The path or URL to your OpenAPI spec file (e.g. `./openapi.yaml`) |

> **Why variables and not secrets?** These values are not sensitive credentials — they are configuration. GitHub Actions variables (not secrets) are the right place for them, and they can be referenced in your workflow with `${{ vars.VARIABLE_NAME }}`.

### Step 3 — Add the action to your workflow

Open your workflow file (e.g. `.github/workflows/test.yml`) and add two steps: one to **start** the proxy before your tests, and one to **stop** it at the end.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # 1. Start the proxy — must come before any steps you want to monitor
      - name: Start API Dependency Monitor
        uses: talK951/API-Dependency-Monitor@main
        with:
          backend_url: ${{ vars.BACKEND_URL }}
          path_to_api_spec: ${{ vars.PATH_TO_API_SPEC }}

      # 2. Your existing steps — no changes needed, traffic is intercepted automatically
      - name: Run tests
        run: npm test

      # 3. Stop the proxy and print the validation report
      #    if: always() ensures this runs even if an earlier step fails
      - name: Stop API Dependency Monitor
        uses: talK951/API-Dependency-Monitor/stop_proxy@main
        if: always()
```

That's it. Push the workflow and the action will start monitoring on the next run.

---

## Inputs

These are passed to the start action via the `with:` block.

| Input | Required | Description |
|---|---|---|
| `backend_url` | No | URL of your self-hosted backend instance |
| `path_to_api_spec` | No | Path or URL to your OpenAPI spec file |
| `host_name` | No | If set, only requests to this hostname are monitored (e.g. `api.example.com`) |

---

## Reading the output

After the stop step runs, the Actions log will show a JSON summary followed by a line-by-line breakdown of every captured request.

**Summary**
```json
{
  "captured": 5,
  "passed": 4,
  "failed": 1
}
```

**Per-request breakdown**

| Indicator | Meaning |
|---|---|
| `✅` | Request matches the OpenAPI spec |
| `❌` | Request violates the spec (wrong endpoint, missing param, bad schema, etc.) |
| `⚠️` | Request could not be validated — usually a network error reaching the backend |

If `failed` is greater than zero, the summary is emitted as a GitHub Actions warning annotation (visible in the PR check summary) and the job exits with code `1`, failing the pipeline.

---

## How traffic interception works

When the start action runs it sets two standard environment variables:

```
HTTP_PROXY=http://localhost:8080
HTTPS_PROXY=http://localhost:8080
```

These are respected automatically by virtually every HTTP client — curl, Python requests, npm, wget, and most language-level HTTP libraries — so all outbound traffic from your subsequent steps flows through the proxy without any code changes on your end.

The action also installs the mitmproxy CA certificate into the system trust store so HTTPS connections can be intercepted and read without TLS errors.
