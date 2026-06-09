import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from dotenv import load_dotenv
from registration import Registration
import requests

load_dotenv()

def test_registration_reads_env_variables():
    os.environ["BACKEND_URL"] = "http://test-backend.com"
    os.environ["ORG_ID"] = "123"
    os.environ["REPO_NAME"] = "test-project"
    os.environ["ORG_NAME"] = "test-org"
    os.environ["USER_ID"] = "456"
    os.environ["USERNAME"] = "test-user"

    registration = Registration(
        org_id=int(os.getenv("ORG_ID")), 
        project_name=os.getenv("REPO_NAME"), 
        org_name=os.getenv("ORG_NAME"), 
        user_id=int(os.getenv("USER_ID")), 
        username=os.getenv("USERNAME")
    )

    assert registration.backend_url == "http://test-backend.com"
    assert registration.org_id == 123
    assert registration.project_name == "test-project"
    assert registration.org_name == "test-org"
    assert registration.user_id == 456
    assert registration.username == "test-user"

BACKEND = "https://scrawny-ashes-reversion.ngrok-free.dev/API-Management-Server"

def register_consumer(org_id, org_name, project_name, user_id, username):
    response = requests.post(
        f"{BACKEND}/RegisterConsumer",
        params={
            "orgId": org_id,
            "orgName": org_name,
            "projectName": project_name,
            "userId": user_id,
            "userName": username,
        },
        headers={"Content-Type": "text/plain"},
    )
    print(f"[{org_name}/{project_name}] status={response.status_code} body={response.text}")
    return response


def register_provider(org_id, org_name, project_name, user_id, username, hostname):
    response = requests.post(
        f"{BACKEND}/RegisterProvider",
        params={
            "orgId": org_id,
            "orgName": org_name,
            "projectName": project_name,
            "userId": user_id,
            "userName": username,
            "hostName": hostname,
        },
        headers={"Content-Type": "text/plain"},
        data="openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths: {}"
    )
    print(f"[{org_name}/{project_name}] status={response.status_code} body={response.text}")
    return response


def test_register_provider():
    response = register_provider(
        org_id=1, org_name="org1", project_name="test-project1",
        user_id=1, username="user1", hostname="https://github.com"
    )
    assert response.status_code == 200


def test_register_provider_different_org():
    response = register_provider(
        org_id=2, org_name="org2", project_name="test-project1",
        user_id=2, username="user2", hostname="https://github.com"
    )
    assert response.status_code == 200


def test_register_provider_different_host():
    response = register_provider(
        org_id=3, org_name="org3", project_name="test-project1",
        user_id=3, username="user3", hostname="https://github.enterprise.com"
    )
    assert response.status_code == 200


def test_register_provider_same_org_multiple_projects():
    # A user belongs to one org but can have many projects
    response1 = register_provider(
        org_id=4, org_name="org4", project_name="project-alpha",
        user_id=4, username="user4", hostname="https://github.com"
    )
    response2 = register_provider(
        org_id=4, org_name="org4", project_name="project-beta",
        user_id=4, username="user4", hostname="https://github.com"
    )
    response3 = register_provider(
        org_id=4, org_name="org4", project_name="project-gamma",
        user_id=4, username="user4", hostname="https://github.com"
    )
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 200


def test_register_consumer():
    response = register_consumer(
        org_id=10, org_name="consumer-org1", project_name="consumer-project1",
        user_id=10, username="consumer-user1"
    )
    assert response.status_code == 200


def test_register_consumer_different_org():
    response = register_consumer(
        org_id=11, org_name="consumer-org2", project_name="consumer-project1",
        user_id=11, username="consumer-user2"
    )
    assert response.status_code == 200


def test_register_consumer_same_org_multiple_projects():
    # A consumer user belongs to one org but can consume many projects
    response1 = register_consumer(
        org_id=12, org_name="consumer-org3", project_name="consumed-project-alpha",
        user_id=12, username="consumer-user3"
    )
    response2 = register_consumer(
        org_id=12, org_name="consumer-org3", project_name="consumed-project-beta",
        user_id=12, username="consumer-user3"
    )
    response3 = register_consumer(
        org_id=12, org_name="consumer-org3", project_name="consumed-project-gamma",
        user_id=12, username="consumer-user3"
    )
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 200


def test_register_consumer_idempotent():
    # Registering the same consumer twice should not fail
    response1 = register_consumer(
        org_id=13, org_name="consumer-org4", project_name="consumer-project1",
        user_id=13, username="consumer-user4"
    )
    response2 = register_consumer(
        org_id=13, org_name="consumer-org4", project_name="consumer-project1",
        user_id=13, username="consumer-user4"
    )
    assert response1.status_code == 200
    assert response2.status_code == 200




