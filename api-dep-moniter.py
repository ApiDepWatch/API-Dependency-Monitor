import asyncio
import os
import sys
import signal
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
from moniter import APIDependencyMonitor
from dotenv import load_dotenv


async def start_proxy_and_monitor_traffic(port: int, org_id: int, project_name: str):
    mitmproxy_config = options.Options(listen_port=port)
    mitmproxy_engine = DumpMaster(mitmproxy_config)
    traffic_monitor = APIDependencyMonitor(org_id=org_id, project_name=project_name)
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
    project_name = os.getenv("PROJECT_NAME")
    pid = os.getpid()
    print(f"proxy_pid={pid}")
    with open("moniter_pid.txt", "w") as f:
        f.write(str(pid))

    asyncio.run(start_proxy_and_monitor_traffic(port, org_id, project_name))


if __name__ == "__main__":
    load_dotenv()
    parse_args_and_run()
