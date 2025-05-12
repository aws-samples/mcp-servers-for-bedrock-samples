from mcp.server.fastmcp import FastMCP
import httpx
import boto3
import os
import logging

# create MCP server instance
mcp = FastMCP("gamelift_mcp_server")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gamelift_mcp_server")

# define a tool function, expose to client
@mcp.tool()
async def echo(message: str) -> str:
    return f"Echo from MCP server: {message}"

@mcp.tool()
async def get_game_lift_fleets(region: str = 'us-east-1') -> str:
    """Get gamelift fleet list in specific region
    
    Args:
        region: AWS region name, e.g. us-east-1, if not provided, use us-east-1 as default
    """
    client = boto3.client('gamelift', region_name=region, 
                          aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                          aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"))

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
async def get_gamelift_container_fleets(region: str = 'us-east-1') -> str:
    """Get gamelift container fleet list in specific region
    
    Args:
        region: AWS region name, e.g. us-east-1, if not provided, use us-east-1 as default
    """
    client = boto3.client('gamelift', region_name=region, 
                          aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                          aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"))

    response = client.list_container_fleets()
    return response.get('ContainerFleets', [])


@mcp.tool()
async def get_fleet_attributes(fleet_id: str, region: str = 'us-east-1') -> str:
    """Get fleet attributes by fleet id
    
    Args:
        fleet_id: Gamelift fleet id
    """
    client = boto3.client('gamelift', region_name=region, 
                          aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                          aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"))

    response = client.describe_fleet_attributes(FleetIds=[fleet_id])
    return response.get('FleetAttributes', [])


@mcp.tool()
async def get_container_fleet_attributes(fleet_id: str, region: str = 'us-east-1') -> str:
    """Get container fleet attributes by fleet id
    
    Args:
        fleet_id: Gamelift container fleet id
    """
    client = boto3.client('gamelift', region_name=region, 
                          aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                          aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"))

    response = client.describe_container_fleet(FleetId=fleet_id)
    return response.get('ContainerFleet', [])


@mcp.tool()
async def get_compute_auth_token(fleet_id: str, region: str = 'us-east-1', compute_name: str = '') -> str:
    """Get compute auth token by fleet id and compute name
    
    Args:
        fleet_id: Gamelift fleet id
        compute_name: compute name
    """
    client = boto3.client('gamelift', region_name=region, 
                          aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                          aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"))

    # 先获取fleet属性，判断是否为ANYWHERE Fleet
    attr_response = client.describe_fleet_attributes(FleetIds=[fleet_id])
    attrs = attr_response.get('FleetAttributes', [])
    if not attrs or attrs[0].get('ComputeType') != 'ANYWHERE':
        raise Exception('Only ANYWHERE Fleets support compute auth token.')

    response = client.get_compute_auth_token(FleetId=fleet_id, ComputeName=compute_name)
    return response.get('AuthToken', '')


@mcp.tool()
async def get_vpc_peering_connections(fleet_id: str, region: str = 'us-east-1') -> str:
    """Get vpc peering connections by fleet id
    
    Args:
        fleet_id: Gamelift fleet id
    """
    client = boto3.client('gamelift', region_name=region, 
                          aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                          aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"))

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
async def get_builds(region: str = 'us-east-1') -> str:
    """Get builds by region
    
    Args:
        region: AWS region name, e.g. us-east-1, if not provided, use us-east-1 as default
    """
    client = boto3.client('gamelift', region_name=region, 
                          aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                          aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"))

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


# start MCP Server
if __name__ == "__main__":
    mcp.run()
