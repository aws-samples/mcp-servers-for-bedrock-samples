from fastmcp import FastMCP
import os




# Create a calculator MCP server with authentication
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
    
    Authentication is required using a Bearer token in the Authorization header.
    """,
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
    print(f"Starting calculator service with authentication. Set API_TOKEN environment variable to change the default token.")
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8080,
        log_level="debug",
    )