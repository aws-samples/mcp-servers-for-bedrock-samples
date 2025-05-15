from fastmcp import FastMCP
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
import os

from .cognito_auth import CognitoAuthenticator

# Initialize the Cognito authenticator
auth = CognitoAuthenticator()

# Security scheme for Bearer token authentication
security = HTTPBearer()

# Authentication dependency
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Validate the access token from the Authorization header
    """
    token = credentials.credentials
    try:
        # Validate the token with Cognito
        claims = auth.validate_token(token)
        return claims
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Create a calculator MCP server with Cognito authentication
mcp = FastMCP(
    name="CalculatorApp",
    instructions="""
    This is a calculator service that can perform basic arithmetic operations.
    Available operations:
    - Addition: Add two numbers together
    - Subtraction: Subtract one number from another
    - Multiplication: Multiply two numbers together
    - Division: Divide one number by another
    - Power: Raise a number to a power
    - Square Root: Calculate the square root of a number
    
    Please provide the numbers and specify which operation you want to perform.
    
    Authentication is required using a valid AWS Cognito token in the Authorization header.
    """,
)

# Middleware to validate authentication for all requests
@mcp.app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    Middleware to validate authentication for all requests except OPTIONS requests
    """
    if request.method == "OPTIONS":
        # Allow preflight requests without authentication
        return await call_next(request)
        
    # Check if the request path is for MCP
    if not request.url.path.startswith("/mcp"):
        # For non-MCP endpoints, bypass authentication
        return await call_next(request)
    
    # Extract and validate the token
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=401, 
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth.extract_token_from_header(auth_header)
    if not token:
        raise HTTPException(
            status_code=401, 
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Validate the token with Cognito
        auth.validate_token(token)
        # If validation succeeds, proceed with the request
        return await call_next(request)
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

@mcp.tool()
def add(a: float, b: float) -> float:
    """Adds two numbers together."""
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtracts b from a."""
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiplies two numbers together."""
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divides a by b. Returns an error if b is zero."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

@mcp.tool()
def power(base: float, exponent: float) -> float:
    """Raises base to the power of exponent."""
    return base ** exponent

@mcp.tool()
def square_root(number: float) -> float:
    """Calculates the square root of a number."""
    if number < 0:
        raise ValueError("Cannot calculate square root of a negative number")
    return number ** 0.5

if __name__ == "__main__":
    print(f"Starting calculator service with Cognito authentication...")
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8080,
        log_level="debug",
        cors_origins=["*"],  # Adjust this in production
    )
