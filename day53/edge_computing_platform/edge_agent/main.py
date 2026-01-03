import asyncio
import sys

from agent.edge_agent import EdgeAgent

async def main():
    # Parse command line args for configuration
    region = sys.argv[1] if len(sys.argv) > 1 else "datacenter"
    
    # Region configurations
    configs = {
        "datacenter": {
            "location": {"name": "San Francisco DC", "lat": 37.7749, "lon": -122.4194},
            "capabilities": ["gpu", "high-memory"]
        },
        "factory": {
            "location": {"name": "Remote Factory", "lat": 51.5074, "lon": -0.1278},
            "capabilities": ["cpu-only"]
        },
        "mobile": {
            "location": {"name": "Mobile Vehicle", "lat": 40.7128, "lon": -74.0060},
            "capabilities": ["low-power"]
        }
    }
    
    config = configs.get(region, configs["datacenter"])
    
    agent = EdgeAgent(
        control_plane_url="http://localhost:8000",
        location=config["location"],
        capabilities=config["capabilities"]
    )
    
    await agent.start()

if __name__ == "__main__":
    asyncio.run(main())
