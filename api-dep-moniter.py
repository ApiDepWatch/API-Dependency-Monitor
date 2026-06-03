import asyncio
import os
import sys
import signal
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
from moniter import BACKEND_URL, APIDependencyMonitor
from dotenv import load_dotenv

from registration import Registration



async def start_proxy_and_monitor_traffic(
        port: int, 
        org_id: int, 
        project_name: str, 
        org_name: str, 
        user_id: int, 
        username: str
    ):
    
    mitmproxy_config = options.Options(listen_port=port)
    mitmproxy_engine = DumpMaster(mitmproxy_config)
    traffic_monitor = APIDependencyMonitor(
        org_id=org_id, 
        project_name=project_name, 
        org_name=org_name, 
        user_id=user_id, 
        username=username
    )
    mitmproxy_engine.addons.add(traffic_monitor)

    def handle_sigint(_sig, _frame):
        print("SIGINT received, shutting down gracefully...")
        sys.stdout.flush()
        traffic_monitor.output_results()

        exit_code = 0
        for r in traffic_monitor.results:
            if "✅" not in r:
                exit_code = 1

        with open("exit_code.txt", "w") as f:
            f.write(str(exit_code))
        sys.exit(exit_code)

    signal.signal(signal.SIGINT, handle_sigint)

    print(f"Monitor started on port {port}")
    await mitmproxy_engine.run()


def parse_args_and_run():
    

    port = int(os.getenv("PORT"))
    org_id = int(os.getenv("ORG_ID"))
    org_name = os.getenv("ORG_NAME")
    user_id = int(os.getenv("USER_ID"))
    username = os.getenv("USERNAME")
    project_name = os.getenv("REPO_NAME")
    is_provider = os.getenv("IS_PROVIDER").lower() == "true"
    
    
    registration = Registration(
        org_id=org_id, 
        project_name=project_name, 
        org_name=org_name, 
        user_id=user_id, 
        username=username
    )

    registration.registar_repository()
    

    pid = os.getpid()
    print(f"proxy_pid={pid}")
    with open("moniter_pid.txt", "w") as f:
        f.write(str(pid))

    asyncio.run(
        start_proxy_and_monitor_traffic(
            port, 
            org_id, 
            project_name, 
            org_name, 
            user_id, 
            username
        )
    )


if __name__ == "__main__":
    load_dotenv()
    parse_args_and_run()
