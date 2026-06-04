import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from dotenv import load_dotenv
import requests

load_dotenv()

BACKEND = "https://scrawny-ashes-reversion.ngrok-free.dev/API-Management-Server"

# ==============================================================================
# OpenAPI Specs
# ==============================================================================

users_api_spec = """
openapi: 3.0.0
info:
  title: Users API
  version: 1.0.0
paths:
  /users:
    get:
      summary: Get all users
      responses:
        '200':
          description: OK
    post:
      summary: Create a user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - name
                - email
              properties:
                name:
                  type: string
                email:
                  type: string
      responses:
        '201':
          description: Created
  /users/{id}:
    get:
      summary: Get a user by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: OK
        '404':
          description: Not found
"""

products_api_spec = """
openapi: 3.0.0
info:
  title: Products API
  version: 1.0.0
paths:
  /products:
    get:
      summary: List products
      parameters:
        - name: category
          in: query
          required: false
          schema:
            type: string
      responses:
        '200':
          description: OK
    post:
      summary: Create a product
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - name
                - price
              properties:
                name:
                  type: string
                price:
                  type: number
      responses:
        '201':
          description: Created
  /products/{id}:
    get:
      summary: Get a product by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: OK
        '404':
          description: Not found
    delete:
      summary: Delete a product
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '204':
          description: Deleted
"""

# ==============================================================================
# Provider setup helpers
# ==============================================================================

def register_users_api_provider():
    response = requests.post(
        f"{BACKEND}/RegisterProvider",
        params={
            "orgId": 1000,
            "orgName": "verification-test-org",
            "projectName": "users-api",
            "userId": 1000,
            "userName": "verification-test-user",
            "hostName": "users-api-host",
        },
        headers={"Content-Type": "text/plain"},
        data=users_api_spec
    )
    assert response.status_code == 200, f"Provider registration failed: {response.text}"


def register_products_api_provider():
    response = requests.post(
        f"{BACKEND}/RegisterProvider",
        params={
            "orgId": 1001,
            "orgName": "verification-test-org-2",
            "projectName": "products-api",
            "userId": 1001,
            "userName": "verification-test-user-2",
            "hostName": "products-api-host",
        },
        headers={"Content-Type": "text/plain"},
        data=products_api_spec
    )
    assert response.status_code == 200, f"Provider registration failed: {response.text}"


# ==============================================================================
# Verification helper
# ==============================================================================

def verify(project_name, raw_http):
    response = requests.post(
        f"{BACKEND}/IsRequestValid",
        params={"projectName": project_name},
        data=raw_http,
        headers={"Content-Type": "text/plain"},
    )
    print(f"[{project_name}] status={response.status_code} body={response.text}")
    return response


# ==============================================================================
# Users API — valid requests
# ==============================================================================

def test_users_valid_get_all():
    register_users_api_provider()
    raw = (
        "GET /users HTTP/1.1\r\n"
        "Host: users-api-host\r\n"
        "Accept: application/json\r\n"
        "\r\n"
    )
    response = verify("users-api", raw)
    assert response.status_code == 200
    assert "✅" in response.text


def test_users_valid_get_by_id():
    register_users_api_provider()
    raw = (
        "GET /users/42 HTTP/1.1\r\n"
        "Host: users-api-host\r\n"
        "Accept: application/json\r\n"
        "\r\n"
    )
    response = verify("users-api", raw)
    assert response.status_code == 200
    assert "✅" in response.text


def test_users_valid_post_with_body():
    register_users_api_provider()
    body = '{"name": "Alice", "email": "alice@example.com"}'
    raw = (
        "POST /users HTTP/1.1\r\n"
        "Host: users-api-host\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
        f"{body}"
    )
    response = verify("users-api", raw)
    assert response.status_code == 200
    assert "✅" in response.text


# ==============================================================================
# Users API — invalid requests
# ==============================================================================

def test_users_invalid_path():
    register_users_api_provider()
    raw = (
        "GET /nonexistent HTTP/1.1\r\n"
        "Host: users-api-host\r\n"
        "\r\n"
    )
    response = verify("users-api", raw)
    assert response.status_code == 200
    assert "❌" in response.text


def test_users_invalid_method():
    register_users_api_provider()
    # DELETE /users is not defined in the spec
    raw = (
        "DELETE /users HTTP/1.1\r\n"
        "Host: users-api-host\r\n"
        "\r\n"
    )
    response = verify("users-api", raw)
    assert response.status_code == 200
    assert "❌" in response.text


def test_users_invalid_post_missing_required_field():
    register_users_api_provider()
    # Missing required "email" field
    body = '{"name": "Bob"}'
    raw = (
        "POST /users HTTP/1.1\r\n"
        "Host: users-api-host\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
        f"{body}"
    )
    response = verify("users-api", raw)
    assert response.status_code == 200
    assert "❌" in response.text


def test_users_invalid_post_empty_body():
    register_users_api_provider()
    # POST /users requires a body with name and email
    raw = (
        "POST /users HTTP/1.1\r\n"
        "Host: users-api-host\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: 0\r\n"
        "\r\n"
    )
    response = verify("users-api", raw)
    assert response.status_code == 200
    assert "❌" in response.text


# ==============================================================================
# Products API — valid requests
# ==============================================================================

def test_products_valid_get_all():
    register_products_api_provider()
    raw = (
        "GET /products HTTP/1.1\r\n"
        "Host: products-api-host\r\n"
        "Accept: application/json\r\n"
        "\r\n"
    )
    response = verify("products-api", raw)
    assert response.status_code == 200
    assert "✅" in response.text


def test_products_valid_get_all_with_query_param():
    register_products_api_provider()
    raw = (
        "GET /products?category=electronics HTTP/1.1\r\n"
        "Host: products-api-host\r\n"
        "Accept: application/json\r\n"
        "\r\n"
    )
    response = verify("products-api", raw)
    assert response.status_code == 200
    assert "✅" in response.text


def test_products_valid_get_by_id():
    register_products_api_provider()
    raw = (
        "GET /products/7 HTTP/1.1\r\n"
        "Host: products-api-host\r\n"
        "Accept: application/json\r\n"
        "\r\n"
    )
    response = verify("products-api", raw)
    assert response.status_code == 200
    assert "✅" in response.text


def test_products_valid_post():
    register_products_api_provider()
    body = '{"name": "Widget", "price": 9.99}'
    raw = (
        "POST /products HTTP/1.1\r\n"
        "Host: products-api-host\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
        f"{body}"
    )
    response = verify("products-api", raw)
    assert response.status_code == 200
    assert "✅" in response.text


def test_products_valid_delete():
    register_products_api_provider()
    raw = (
        "DELETE /products/3 HTTP/1.1\r\n"
        "Host: products-api-host\r\n"
        "\r\n"
    )
    response = verify("products-api", raw)
    assert response.status_code == 200
    assert "✅" in response.text


# ==============================================================================
# Products API — invalid requests
# ==============================================================================

def test_products_invalid_path():
    register_products_api_provider()
    raw = (
        "GET /orders HTTP/1.1\r\n"
        "Host: products-api-host\r\n"
        "\r\n"
    )
    response = verify("products-api", raw)
    assert response.status_code == 200
    assert "❌" in response.text


def test_products_invalid_post_missing_price():
    register_products_api_provider()
    # Missing required "price" field
    body = '{"name": "Widget"}'
    raw = (
        "POST /products HTTP/1.1\r\n"
        "Host: products-api-host\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        "\r\n"
        f"{body}"
    )
    response = verify("products-api", raw)
    assert response.status_code == 200
    assert "❌" in response.text


def test_products_invalid_delete_on_collection():
    register_products_api_provider()
    # DELETE /products (without ID) is not in the spec
    raw = (
        "DELETE /products HTTP/1.1\r\n"
        "Host: products-api-host\r\n"
        "\r\n"
    )
    response = verify("products-api", raw)
    assert response.status_code == 200
    assert "❌" in response.text
