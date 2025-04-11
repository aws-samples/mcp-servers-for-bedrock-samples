#!/usr/bin/env python3
import json
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP, Context
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

mcp = FastMCP("timer-server")

def get_local_tz(local_tz_override: str | None = None) -> ZoneInfo:

    # Get local timezone from datetime.now()
    tzinfo = datetime.now().astimezone(tz=None).tzinfo
    if tzinfo is not None:
        tz_str = str(tzinfo)
        if tz_str == "CST":
            tz_str = "America/Chicago" 

        return ZoneInfo(tz_str)
    else:
        raise ValueError('get local timezone failed')
        

def get_zoneinfo(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except Exception as e:
        raise ValueError(f"Invalid timezone: {str(e)}")

def update_docstring_with_info(func):
    """更新函数的docstring，"""
    local_tz = str(get_local_tz())
    
    if func.__doc__:
        func.__doc__ = func.__doc__.format(
            local_tz=local_tz
        )
    return func

@mcp.tool()
@update_docstring_with_info
def get_current_time(timezone_name: str) -> str:
    """Get current time in specified timezone
    
    Args:
        timezone_name: IANA timezone name (e.g., 'America/New_York', 'Europe/London'). Use '{local_tz}' as local timezone if no timezone provided by the user."
    
    """
    timezone = get_zoneinfo(timezone_name)
    current_time = datetime.now(timezone)

    return json.dumps(dict(
        timezone=timezone_name,
        datetime=current_time.isoformat(timespec="seconds"),
        is_dst=bool(current_time.dst()),
    ),ensure_ascii=False)
    
    
if __name__ == "__main__":
    mcp.run()
    # print(get_current_time("Asia/Shanghai"))
    