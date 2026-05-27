import requests as http_requests
from mitmproxy import http

BACKEND_URL = "https://localhost:8080/API-Management-Server"

class APIDependencyMonitor:
    def __init__(self, org_id: int = None, project_name: str = None):
        self.requests_log = []
        self.org_id = org_id
        self.project_name = project_name
        self.results = []

    def request(self, flow: http.HTTPFlow):
        raw_http_request = self._format_request_as_raw_http(flow.request)
        self.requests_log.append(raw_http_request)
        if self.org_id is not None and self.project_name:
            self._validate_request_against_openapi_spec(raw_http_request)

    def _format_request_as_raw_http(self, req) -> str:
        headers = "\n".join(f"{k}: {v}" for k, v in req.headers.items())
        body = req.text or ""
        return f"{req.method} {req.pretty_url} {req.http_version}\n{headers}\n\n{body}\n"

    def _validate_request_against_openapi_spec(self, raw_http_request: str):
        try:
            response = http_requests.post(
                f"{BACKEND_URL}/IsRequestValid",
                params={"orgId": self.org_id, "projectName": self.project_name},
                data=raw_http_request,
                headers={"Content-Type": "text/plain"},
            )
            self.results.append(f"{raw_http_request.splitlines()[0]} -> {response.text}")
        except Exception as e:
            self.results.append(f"{raw_http_request.splitlines()[0]} -> Error occurred while validating request")