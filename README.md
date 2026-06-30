# API Dependency Monitor

A GitHub Action that intercepts every outbound HTTP and HTTPS request your integration tests make and checks them against your API provider's latest OpenAPI specification — notifying you of upcoming changes so you can update before anything breaks.


## Table of Contents

- [What is it?](#what-is-it)
- [Who is this for?](#who-is-this-for)
- [Provider vs Consumer — understanding your role](#provider-vs-consumer--understanding-your-role)
- [How it works](#how-it-works)
- [Setup](#setup)
  - [Prerequisites — deploy the backend once](#prerequisites--deploy-the-backend-once)
  - [Provider Setup](#provider-setup--you-own-the-api)
  - [Consumer Setup](#consumer-setup--you-call-someone-elses-api)
  - [Adding the action to your workflow](#adding-the-action-to-your-workflow)
- [Reading the output](#reading-the-output)
- [How traffic interception works](#how-traffic-interception-works)
- [Technical Demo](#technical-demo)

---

## Technical Demo

Watch a full walkthrough of how the action works in a real CI pipeline:

[![API Dependency Monitor Demo](https://img.youtube.com/vi/MzkYNd5_HZs/0.jpg)](https://youtu.be/MzkYNd5_HZs)

---

## What is it?

When API providers release updates to their services, they publish a new OpenAPI specification describing what has changed. This action sits inside your CI pipeline and automatically compares the HTTP requests your tests make against that latest spec. If your requests no longer match the newest version, your job flags it — giving you an early warning that the provider is rolling out changes and your code will need to catch up.

Nothing is broken yet. This is a heads-up, not an error.

This is a **self-hosted** solution built around a single shared backend instance. The **[API Dependency Management Platform Backend](https://github.com/ApiDepWatch/API-Dependency-Management-Platform-Backend)** is deployed once for the entire company — every provider and every consumer team then plugs into that same instance. The backend handles all the coordination automatically.


## Who is this for?

This tool is built for companies that maintain multiple services that communicate with each other through REST APIs — where one team's changes can affect another team's code.

In that environment, coordinating API changes is painful. A backend team updates their spec, and now they have to track down every consumer team, send Slack messages, write emails, and hope everyone updates in time. It is slow, error-prone, and easy to miss.

This action removes that burden entirely. The coordination happens automatically through the pipeline. When a provider updates their OpenAPI spec, every consumer team with this action in their workflow gets notified on their next CI run — their job flags exactly which of their HTTP calls no longer match the latest spec, and exactly where in their codebase those calls are made. No chasing people down. No missed updates. The pipeline does the work.

## Provider vs Consumer — understanding your role

These two roles describe your relationship to the API being monitored and determine how you configure the action.

**A provider** owns the API. You point the action at your OpenAPI spec file and the backend stays up to date automatically every time your workflow runs. When you release a new version of your spec, any consumer who has this action in their pipeline will be notified on their next run — their job flags which of their requests no longer match your newest spec, showing them exactly which calls need to change and where they are in their code.

**A consumer** calls someone else's API. You add this action to your pipeline with just the shared backend URL. Every time your tests run, the action intercepts your outbound requests and checks them against the provider's latest spec on the backend. If the provider has released an update that affects your calls, your job flags it — so you know exactly what to update and you have time to do it before the change goes live.

> **Note:** A provider can also be a consumer. If your service calls other APIs in its own tests, you can monitor those calls too by pointing the action at the relevant spec.

## How it works

1. A mitmproxy-based HTTP proxy starts in the background at the beginning of your job
2. All outbound HTTP and HTTPS traffic is automatically routed through it — your actual calls are never interrupted or modified
3. Each intercepted request is sent to the shared company backend, which looks up the provider's latest registered OpenAPI spec and compares the request against it
4. When your job finishes, the proxy shuts down and prints a full summary: every request captured, whether it matched the latest spec or not, and what the difference was
5. If any requests don't match the latest spec, the job exits with a non-zero code — this is your notification that the provider has updated or is releasing an update to their API and your code should be reviewed and updated accordingly. A passing job means all your requests are fully in line with the provider's latest specification


## Setup

### Prerequisites — deploy the backend once

Before any team can use this action, your company needs one running instance of the **[API Dependency Management Platform Backend](https://github.com/talK951/API-Dependency-Management-Platform-Backend)**. This is a one-time setup done once for the whole company. Follow the instructions in that repository to get it running. Once it is up you will have a `BACKEND_URL` — the shared URL that every provider and consumer team will use.


### Provider Setup — You own the API

All you need to do is add the action to your workflow and point it at your OpenAPI spec file. The backend will stay up to date automatically every time your workflow runs. When you release a new spec, consumer pipelines will pick it up on their next run with no action required from you.

**Step 1 — Add repository variables**

In your repository go to **Settings → Secrets and variables → Actions → Variables → New repository variable** and add the following:

| Name | Value |
|---|---|
| `BACKEND_URL` | The shared company backend URL (get this from whoever manages the backend) |
| `PATH_TO_API_SPEC` | The path to your OpenAPI spec file within the repository (e.g. `./openapi.yaml`) |
| `HOST_NAME` | The hostname consumers use to call your API (e.g. `api.example.com`) |

**Step 2 — Add the action to your workflow**

See the [workflow example below](#adding-the-action-to-your-workflow).



### Consumer Setup — You call someone else's API

You do not need to deploy anything or register anything. You just need the shared `BACKEND_URL` and then you add the action to your workflow. Every time your pipeline runs, the action will automatically compare your outbound requests against the latest spec for every API you call, and notify you if anything has changed.

**Step 1 — Get the shared backend URL**

Ask your platform or infrastructure team for the shared `BACKEND_URL`.

**Step 2 — Add it as a repository variable**

In your repository go to **Settings → Secrets and variables → Actions → Variables → New repository variable** and add the following:

| Name | Value |
|---|---|
| `BACKEND_URL` | The shared company backend URL |

> **Why a variable and not a secret?** This value is not a sensitive credential — it is configuration. GitHub Actions variables (not secrets) are the right place for it, and it can be referenced in your workflow with `${{ vars.BACKEND_URL }}`.

**Step 3 — Add the action to your workflow**

See the [workflow example below](#adding-the-action-to-your-workflow).

---

### Adding the action to your workflow

This step is the same for both providers and consumers. Open your workflow file (e.g. `.github/workflows/test.yml`) and add the two steps below — one to start the proxy before your tests and one to stop it at the end.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Step 1: Start the proxy
      # Must come before any steps that make HTTP requests you want to monitor
      - name: Start API Dependency Monitor
        uses: ApiDepWatch/API-Dependency-Monitor@latest
        with:
          backend_url: ${{ vars.BACKEND_URL }}
          path_to_api_spec: ${{ vars.PATH_TO_API_SPEC }}  # Providers only — omit if you are a consumer
          host_name: ${{ vars.HOST_NAME }}                # Providers only — omit if you are a consumer

      # Step 2: Run your tests
      # No changes needed here — all outbound HTTP/HTTPS traffic is intercepted automatically
      - name: Run tests
        run: ...

      # Step 3: Stop the proxy and print the notification report
      # if: always() ensures this runs even when earlier steps fail
      - name: Stop API Dependency Monitor
        uses: ApiDepWatch/API-Dependency-Monitor/stop_proxy@latest
        if: always()
```

Push the workflow. On the next run the action will start the proxy, route all outbound traffic through it, compare every request against the latest registered OpenAPI spec on the shared backend, and print a full report when your tests finish. If any requests don't match the latest spec, the job will flag them with a clear breakdown of what has changed and what you should review.

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
| `✅` | Request matches the provider's latest OpenAPI spec — nothing to update |
| `❌` | Request does not match the latest spec — the provider has released or is releasing an update that affects this request |
| `⚠️` | Request could not be validated — the provider of this API is not registered in the system |

If any requests are flagged with `❌`, the job exits with code `1`. This is your notification to review the provider's latest spec and update your code accordingly.


## How traffic interception works

When the start action runs it sets two standard environment variables:

```
HTTP_PROXY=http://localhost:8080
HTTPS_PROXY=http://localhost:8080
```

These are respected automatically by virtually every HTTP client — curl, Python requests, npm, wget, and most language-level HTTP libraries — so all outbound traffic from your subsequent steps flows through the proxy without any code changes on your end.

The action also installs the mitmproxy CA certificate into the system trust store so HTTPS connections can be intercepted and read without TLS errors.
