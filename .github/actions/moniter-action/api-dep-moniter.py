import asyncio
import argparse
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
from moniter import APIDependencyMonitor
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

    print(f"\nCaptured {len(traffic_monitor.requests_log)} requests.")
    print("Validation Results:")
    for result in traffic_monitor.results:
        print(result)

def parse_args_and_run():
    parser = argparse.ArgumentParser(description="API Dependency Monitor")
    parser.add_argument("--port", type=int, required=True, help="Port to listen on")
    parser.add_argument("--orgId", type=int, required=True, help="Organization ID")
    parser.add_argument("--projectName", type=str, required=True, help="Project Name")
    args = parser.parse_args()

    try:
        asyncio.run(start_proxy_and_monitor_traffic(args.port, args.orgId, args.projectName))
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    load_dotenv()
    parse_args_and_run()
