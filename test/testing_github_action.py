import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import responses as responses_mock
from dotenv import load_dotenv

load_dotenv()  # must run before moniter is imported so its module-level BACKEND_URL is set

from moniter import APIDependencyMonitor, output_results_and_exit
BACKEND_URL = os.getenv("BACKEND_URL")
orgId = 1
projectName = "test-project"


@responses_mock.activate
def test_validate_request_records_valid_result():
    responses_mock.add(
        responses_mock.POST,
        f"{BACKEND_URL}/IsRequestValid",
        body="✅ Request matches spec.",
        status=200,
    )

    request_ = "POST https://example.com HTTP/1.1\n\n\n"

    monitor = APIDependencyMonitor(org_id=orgId, project_name=projectName)
    monitor._validate_request_against_openapi_spec(request_)

    print(f"Results: {monitor.results}")


    assert len(monitor.results) == 1
    assert "✅ Request matches spec." in monitor.results[0]


@responses_mock.activate
def test_validate_request_records_invalid_result():
    responses_mock.add(
        responses_mock.POST,
        f"{BACKEND_URL}/IsRequestValid",
        body="❌ Request does not match spec.",
        status=200,
    )
    request_ = "POST https://example.com HTTP/1.1\n\n\n"
    monitor = APIDependencyMonitor(org_id=orgId, project_name=projectName)
    monitor._validate_request_against_openapi_spec(request_)

    print(f"Results: {monitor.results}")

    assert len(monitor.results) == 1
    assert f"❌ Request does not match spec." in monitor.results[0]


@responses_mock.activate
def test_validate_request_handles_network_error():
    responses_mock.add(
        responses_mock.POST,
        f"{BACKEND_URL}/IsRequestValid",
        body=Exception("connection refused"),
    )

    request_ = "POST https://example.com HTTP/1.1\n\n\n"
    monitor = APIDependencyMonitor(org_id=orgId, project_name=projectName)
    monitor._validate_request_against_openapi_spec(request_)

    assert len(monitor.results) == 1
    assert f"Error occurred while validating request" in monitor.results[0]


def test_requests_log_starts_empty():
    monitor = APIDependencyMonitor(org_id=orgId, project_name=projectName)
    assert monitor.requests_log == []


def test_results_start_empty():
    monitor = APIDependencyMonitor(org_id=orgId, project_name=projectName)
    assert monitor.results == []


def test_init_stores_org_id_and_project_name():
    monitor = APIDependencyMonitor(org_id=42, project_name="my-project")
    assert monitor.org_id == 42
    assert monitor.project_name == "my-project"



@responses_mock.activate
def test_validate_request_records_multiple_invalid_results():
    responses_mock.add(
        responses_mock.POST,
        f"{BACKEND_URL}/IsRequestValid",
        body="❌ Request does not match spec.",
        status=200,
    )

    request_ = "POST https://example.com HTTP/1.1\n\n\n"

    monitor = APIDependencyMonitor(org_id=orgId, project_name=projectName)

    number_of_requests_made = 5
    for _ in range(number_of_requests_made):
        monitor._validate_request_against_openapi_spec(request_)
    

    print(f"Results: {monitor.results}")


    assert len(monitor.results) == number_of_requests_made

    for i in range(number_of_requests_made):
        assert "❌ Request does not match spec." in monitor.results[i] 

@responses_mock.activate
def test_validate_request_records_multiple_valid_results():
    responses_mock.add(
        responses_mock.POST,
        f"{BACKEND_URL}/IsRequestValid",
        body="✅ Request matches spec.",
        status=200,
    )

    request_ = "POST https://example.com HTTP/1.1\n\n\n"

    monitor = APIDependencyMonitor(org_id=orgId, project_name=projectName)

    number_of_requests_made = 5
    for _ in range(number_of_requests_made):
        monitor._validate_request_against_openapi_spec(request_)
    

    print(f"Results: {monitor.results}")


    assert len(monitor.results) == number_of_requests_made

    for i in range(number_of_requests_made):
        assert "✅ Request matches spec." in monitor.results[i]


# ==============================================================================
# output_results_and_exit tests
# ==============================================================================

def test_output_exits_0_when_all_passed():
    monitor = APIDependencyMonitor(org_id=orgId, project_name=projectName)
    monitor.results = [
        "GET https://example.com HTTP/1.1 -> ✅ Request matches spec.",
        "POST https://example.com HTTP/1.1 -> ✅ Request matches spec.",
    ]
    with pytest.raises(SystemExit) as exc:
        output_results_and_exit(monitor)
    assert exc.value.code == 0


def test_output_exits_1_when_any_failed():
    monitor = APIDependencyMonitor(org_id=orgId, project_name=projectName)
    monitor.results = [
        "GET https://example.com HTTP/1.1 -> ✅ Request matches spec.",
        "POST https://example.com HTTP/1.1 -> ❌ Request does not match spec.",
    ]
    with pytest.raises(SystemExit) as exc:
        output_results_and_exit(monitor)
    assert exc.value.code == 1


def test_output_exits_1_when_all_failed():
    monitor = APIDependencyMonitor(org_id=orgId, project_name=projectName)
    monitor.results = [
        "GET https://example.com HTTP/1.1 -> ❌ Request does not match spec.",
        "POST https://example.com HTTP/1.1 -> ❌ Request does not match spec.",
    ]
    with pytest.raises(SystemExit) as exc:
        output_results_and_exit(monitor)
    assert exc.value.code == 1


def test_output_exits_0_when_no_results():
    monitor = APIDependencyMonitor(org_id=orgId, project_name=projectName)
    with pytest.raises(SystemExit) as exc:
        output_results_and_exit(monitor)
    assert exc.value.code == 0