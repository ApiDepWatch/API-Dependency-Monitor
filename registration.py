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

        print("backend_url=", self.backend_url)
        print("is_provider=", self.is_provider)
        print("org_id=", self.org_id)
        print("project_name=", self.project_name)
        print("org_name=", self.org_name)
        print("user_id=", self.user_id)
        print("username=", self.username)


    def registar_repository(self):
        if self.is_provider:
            print("Registering provider repository with backend...")
            self.registar_provider_repository_with_backend()
        else:
            print("Registering consumer repository with backend...")
            self.registar_consumer_repository_with_backend()

    def registar_provider_repository_with_backend(self):
        try:
            specfile = ""
            with open(os.getenv("PATH_TO_API_SPEC")) as f:
                specfile = f.read()
            print("====================\n")
            print("API Spec file content:")
            print(specfile)
            print("====================\n")

            params = {
                "orgId": self.org_id,
                "projectName": self.project_name,
                "orgName": self.org_name,
                "userId": self.user_id,
                "userName": self.username,
                "hostName": os.getenv("HOST_NAME")
            }


            print("====================================\n")
            print("RegisterProvider request:")
            print(f"  url={self.backend_url}/RegisterProvider")
            print(f"  params={params}")
            print("  data=SPECFILEEEEE")
            print("====================================\n")
            
            response = http_requests.post(
                f"{self.backend_url}/RegisterProvider",
                params=params,
                headers={"Content-Type": "application/json"},
                data=specfile
            )
            print(f"RegisterProvider response: status={response.status_code} body={response.text}")
        except Exception as e:
            print(f"Error occurred while registering provider repository with backend: {e}")

    def registar_consumer_repository_with_backend(self):
        try:
            params={
                "orgId": self.org_id, 
                "projectName": self.project_name, 
                "orgName": self.org_name, 
                "userId": self.user_id, 
                "userName": self.username
            }

            print("====================================\n")
            print("RegisterConsumer request:")
            print(f"  url={self.backend_url}/RegisterConsumer")
            print(f"  params={params}")
            print("====================================\n")

            response = http_requests.post(
                f"{self.backend_url}/RegisterConsumer",
                params=params,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                print(response.text)
            else:
                print(f"Failed to register consumer repository with backend. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error occurred while registering consumer repository with backend: {e}")
    
