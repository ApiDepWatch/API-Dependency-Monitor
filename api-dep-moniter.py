import asyncio
import os
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
from moniter import APIDependencyMonitor, output_results_and_exit
from dotenv import load_dotenv


async def start_proxy_and_monitor_traffic(port: int, org_id: int, project_name: str):
    mitmproxy_config = options.Options(listen_port=port)
    mitmproxy_engine = DumpMaster(mitmproxy_config)
    traffic_monitor = APIDependencyMonitor(org_id=org_id, project_name=project_name)
    mitmproxy_engine.addons.add(traffic_monitor)

    print(f"Monitor started on port {port}. Press Ctrl+C to stop.")
    try:
        await mitmproxy_engine.run()
    except (KeyboardInterrupt, asyncio.CancelledError):
        mitmproxy_engine.shutdown()

    output_results_and_exit(traffic_monitor)


def parse_args_and_run():
    port = int(os.getenv("PORT"))
    org_id = int(os.getenv("ORG_ID"))
    project_name = os.getenv("PROJECT_NAME")

    try:
        asyncio.run(start_proxy_and_monitor_traffic(port, org_id, project_name))
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    load_dotenv()
    parse_args_and_run()
