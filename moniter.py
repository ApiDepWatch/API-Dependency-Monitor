import requests as http_requests
from mitmproxy import http

BACKEND_URL = "https://api-dependency-management-platform.onrender.com/API-Management-Server"

class APIDependencyMonitor:
    def __init__(self, org_id: int = None, project_name: str = None):
        self.requests_log = []
        self.org_id = org_id
        self.project_name = project_name

    def request(self, flow: http.HTTPFlow):
        req = flow.request
        headers = "\n".join(f"{k}: {v}" for k, v in req.headers.items())
        body = req.text or ""
        raw = f"{req.method} {req.pretty_url} {req.http_version}\n{headers}\n\n{body}\n"
        self.requests_log.append(raw)

        if self.org_id is not None and self.project_name:
            self._validate(raw)

    def _validate(self, raw_request: str):
        try:
            response = http_requests.post(
                f"{BACKEND_URL}/IsRequestValid",
                params={"orgId": self.org_id, "projectName": self.project_name},
                data=raw_request,
                headers={"Content-Type": "text/plain"},
            )
            print(f"{raw_request.splitlines()[0]} -> {response.text}")
        except Exception as e:
            print(f"Validation error: {e}")

addons = [APIDependencyMonitor()]
