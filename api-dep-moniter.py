import asyncio
import argparse
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
from moniter import APIDependencyMonitor

async def start(port: int, org_id: int, project_name: str):
    opts = options.Options(listen_port=port)
    master = DumpMaster(opts)
    addon = APIDependencyMonitor(org_id=org_id, project_name=project_name)
    master.addons.add(addon)

    print(f"Monitor started on port {port}. Press Ctrl+C to stop.")
    try:
        await master.run()
    except KeyboardInterrupt:
        master.shutdown()

    print(f"\nCaptured {len(addon.requests_log)} requests.")

def main():
    parser = argparse.ArgumentParser(description="API Dependency Monitor")
    parser.add_argument("--port", type=int, required=True, help="Port to listen on")
    parser.add_argument("--orgId", type=int, required=True, help="Organization ID")
    parser.add_argument("--projectName", type=str, required=True, help="Project Name")
    args = parser.parse_args()

    asyncio.run(start(args.port, args.orgId, args.projectName))

if __name__ == "__main__":
    main()
