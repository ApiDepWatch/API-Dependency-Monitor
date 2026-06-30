import asyncio
import os
import sys
import signal
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
from moniter import APIDependencyMonitor
from dotenv import load_dotenv

from registration import Registration



async def start_proxy_and_monitor_traffic(
        org_id: int, 
        project_name: str, 
        org_name: str, 
        user_id: int, 
        username: str
    ):
    
    mitmproxy_config = options.Options(listen_port=8080)
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
        sys.stdout.flush()
        traffic_monitor.output_results()

        exit_code = 0
        for r in traffic_monitor.results:
            if "❌" in r:
                exit_code = 1

        with open("exit_code.txt", "w") as f:
            f.write(str(exit_code))
        sys.exit(exit_code)

    signal.signal(signal.SIGINT, handle_sigint)

    await mitmproxy_engine.run()


def parse_args_and_run():
    org_id = int(os.getenv("ORG_ID"))
    org_name = os.getenv("ORG_NAME")
    user_id = int(os.getenv("USER_ID"))
    username = os.getenv("USERNAME")
    project_name = os.getenv("REPO_NAME")
    
    
    pid = os.getpid()
    with open("moniter_pid.txt", "w") as f:
        f.write(str(pid))

    registration = Registration(
        org_id=org_id,
        project_name=project_name,
        org_name=org_name,
        user_id=user_id,
        username=username
    )

    registration.registar_repository()

    asyncio.run(
        start_proxy_and_monitor_traffic(
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
