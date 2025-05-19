from mcp.server.fastmcp import FastMCP
import httpx
import boto3
import os
import logging
from typing import List

# create MCP server instance
mcp = FastMCP("gamelift_mcp_server")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gamelift_mcp_server")

def get_gamelift_client(region: str):
    """Get a GameLift client using either AWS_PROFILE or AWS credentials
    
    Args:
        region: AWS region name
    """
    if os.environ.get("AWS_PROFILE"):
        session = boto3.Session(profile_name=os.environ.get("AWS_PROFILE"))
        return session.client('gamelift', region_name=region)
    else:
        return boto3.client('gamelift', region_name=region,
                          aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                          aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"))

# define a tool function, expose to client
# @mcp.tool()
# async def echo(message: str) -> str:
#     return f"Echo from MCP server: {message}"

@mcp.tool()
async def get_game_lift_fleets(region: str = os.environ.get("AWS_REGION")) -> str:
    """Get gamelift fleet list in specific region
    
    Args:
        region: AWS region name, e.g. us-east-1, if not provided, use us-east-1 as default
    """
    client = get_gamelift_client(region)

    # 1. Get All Fleet ID
    fleet_ids = []
    response = client.list_fleets()
    fleet_ids.extend(response.get('FleetIds', []))

    # pagination
    next_token = response.get('NextToken')
    while next_token:
        response = client.list_fleets(NextToken=next_token)
        fleet_ids.extend(response.get('FleetIds', []))
        next_token = response.get('NextToken')

    logger.info(f"Found {len(fleet_ids)}  Fleet")

    # 2. batch call describe_fleet_attributes to get detailed information (API has a limit on the number of fleets per request, usually up to 100)
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    fleet_details = []
    for chunk_ids in chunks(fleet_ids, 100):
        response = client.describe_fleet_attributes(FleetIds=chunk_ids)
        fleet_details.extend(response.get('FleetAttributes', []))
    
    return fleet_details

@mcp.tool()
async def get_gamelift_container_fleets(region: str = os.environ.get("AWS_REGION")) -> str:
    """Get gamelift container fleet list in specific region
    
    Args:
        region: AWS region name, e.g. us-east-1, if not provided, use us-east-1 as default
    """
    client = get_gamelift_client(region)

    response = client.list_container_fleets()
    return response.get('ContainerFleets', [])


@mcp.tool()
async def get_fleet_attributes(fleet_id: str, region: str = os.environ.get("AWS_REGION")) -> str:
    """Get fleet attributes by fleet id
    
    Args:
        fleet_id: Gamelift fleet id
    """
    client = get_gamelift_client(region)

    response = client.describe_fleet_attributes(FleetIds=[fleet_id])
    return response.get('FleetAttributes', [])


@mcp.tool()
async def get_container_fleet_attributes(fleet_id: str, region: str = os.environ.get("AWS_REGION")) -> str:
    """Get container fleet attributes by fleet id
    
    Args:
        fleet_id: Gamelift container fleet id
    """
    client = get_gamelift_client(region)

    response = client.describe_container_fleet(FleetId=fleet_id)
    return response.get('ContainerFleet', [])


@mcp.tool()
async def get_compute_auth_token(fleet_id: str, region: str = os.environ.get("AWS_REGION"), compute_name: str = '') -> str:
    """Get compute auth token by fleet id and compute name
    
    Args:
        fleet_id: Gamelift fleet id
        compute_name: compute name
    """
    client = get_gamelift_client(region)

    # 先获取fleet属性，判断是否为ANYWHERE Fleet
    attr_response = client.describe_fleet_attributes(FleetIds=[fleet_id])
    attrs = attr_response.get('FleetAttributes', [])
    if not attrs or attrs[0].get('ComputeType') != 'ANYWHERE':
        raise Exception('Only ANYWHERE Fleets support compute auth token.')

    response = client.get_compute_auth_token(FleetId=fleet_id, ComputeName=compute_name)
    return response.get('AuthToken', '')


@mcp.tool()
async def get_vpc_peering_connections(fleet_id: str, region: str = os.environ.get("AWS_REGION")) -> str:
    """Get vpc peering connections by fleet id
    
    Args:
        fleet_id: Gamelift fleet id
    """
    client = get_gamelift_client(region)

    connections = []
    next_token = None
    while True:
        if next_token:
            response = client.describe_vpc_peering_connections(FleetId=fleet_id, NextToken=next_token)
        else:
            response = client.describe_vpc_peering_connections(FleetId=fleet_id)
        connections.extend(response.get('VpcPeeringConnections', []))
        next_token = response.get('NextToken')
        if not next_token:
            break
    return connections


@mcp.tool()
async def get_builds(region: str = os.environ.get("AWS_REGION")) -> str:
    """Get builds by region
    
    Args:
        region: AWS region name, e.g. us-east-1, if not provided, use us-east-1 as default
    """
    client = get_gamelift_client(region)

    builds = []
    next_token = None
    while True:
        if next_token:
            response = client.list_builds(NextToken=next_token)
        else:
            response = client.list_builds()
        builds.extend(response.get('Builds', []))
        next_token = response.get('NextToken')
        if not next_token:
            break
    return builds


@mcp.tool()
async def get_fleet_capacity(fleet_id_list: List[str], region: str = os.environ.get("AWS_REGION")) -> str:
    """Get fleet capacity by fleet id
    
    Args:
        fleet_id: Gamelift fleet id
    """
    client = get_gamelift_client(region)
    
    # check fleet is not a ANYWHERE Fleet
    for fleet_id in fleet_id_list:
        attr_response = client.describe_fleet_attributes(FleetIds=[fleet_id])
        attrs = attr_response.get('FleetAttributes', [])
        if not attrs or attrs[0].get('ComputeType') == 'ANYWHERE':
            raise Exception('ANYWHERE Fleets do not support fleet capacity.')
    
    builds = []
    next_token = None
    while True:
        if next_token:
            response = client.describe_fleet_capacity(FleetIds=fleet_id_list, NextToken=next_token)
        else:
            response = client.describe_fleet_capacity(FleetIds=fleet_id_list)
        builds.extend(response.get('FleetCapacity', []))
        next_token = response.get('NextToken')
        if not next_token:
            break
    return builds


# start MCP Server
if __name__ == "__main__":
    mcp.run()
