import os
import requests as http_requests


class Registration:
    def __init__(self, org_id: int, project_name: str, org_name: str, user_id: int, username: str):
        self.backend_url = os.getenv("BACKEND_URL")
        self.is_provider = os.getenv("IS_PROVIDER").lower() == "true"
        self.org_id = org_id
        self.project_name = project_name
        self.org_name = org_name
        self.user_id = user_id
        self.username = username

    def registar_repository(self):
        if self.is_provider:
            self.registar_provider_repository_with_backend()
        else:
            self.registar_consumer_repository_with_backend()

    def registar_provider_repository_with_backend(self):
        try:
            specfile = ""
            with open(os.getenv("PATH_TO_API_SPEC")) as f:
                specfile = f.read()

            response = http_requests.post(
                f"{self.backend_url}/RegisterProvider",
                params={
                    "orgId": self.org_id, 
                    "projectName": self.project_name, 
                    "orgName": self.org_name, 
                    "userId": self.user_id, 
                    "username": self.username,
                    "openApiSpec": specfile
                    },
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                print(response.text)
            else:
                print(f"Failed to register provider repository with backend. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error occurred while registering provider repository with backend: {e}")

    def registar_consumer_repository_with_backend(self):
        try:
            response = http_requests.post(
                f"{self.backend_url}/RegisterConsumer",
                params={
                    "orgId": self.org_id, 
                    "projectName": self.project_name, 
                    "orgName": self.org_name, 
                    "userId": self.user_id, 
                    "username": self.username
                    },
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                print(response.text)
            else:
                print(f"Failed to register consumer repository with backend. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error occurred while registering consumer repository with backend: {e}")
    
