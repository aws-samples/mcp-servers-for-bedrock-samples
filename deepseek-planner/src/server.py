#!/usr/bin/env python3
import os
import json
import boto3
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP, Context
from botocore.client import Config
# import dotenv
# dotenv.load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("deepseek-planner")
custom_config = Config(connect_timeout=840, read_timeout=840)
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 16000))
# Initialize AWS Bedrock client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),  # Optional
    config=custom_config,
)

# DeepSeek model ID on Bedrock
DEEPSEEK_MODEL_ID = "us.deepseek.r1-v1:0"

def invoke_deepseek(messages: List[Dict[str, str]], 
                   temperature: float = 0.7, 
                   max_tokens: int = 2048
                   ) -> str:
    """
    Invoke the DeepSeek model via AWS Bedrock using the converse API
    """
    try:
        # Prepare the request body
        body = {
            "modelId": DEEPSEEK_MODEL_ID,
            "messages": messages[1:],
            "system": messages[0]['content'],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature,
            }
        }

        response = bedrock_runtime.converse(
            **body
        )

        # Parse the response
        text = [content["text"] for content in response["output"]["message"]["content"] if "text" in content][0]
        return text
    
    except Exception as e:
        print(f"Error invoking DeepSeek model: {e}")
        raise

@mcp.tool()
async def generate_plan(requirements: str, 
                       context: Optional[str] = None, 
                       format: str = "markdown") -> str:
    """Generate a detailed project plan based on requirements.
    
    Args:
        requirements: Project requirements and goals
        context: Additional context or constraints (optional)
        format: Output format (markdown, json, or text)
    """
    try:
        # Prepare messages for DeepSeek
        messages = [
            {
                "role": "system",
                "content": [{"text":"You are an expert project planner. Your task is to create detailed, actionable project plans based on requirements. Be thorough, practical, and consider all aspects of project planning including timeline, resources, milestones, and potential challenges."}]
            },
            {
                "role": "user",
                "content": [{"text":f"Please create a detailed project plan for the following requirements:\n\n{requirements}\n\n" + f'Additional context: {context}\n\n' if context else '' + f"Please provide the plan in {format} format."}]
            }
        ]

        # Invoke DeepSeek model
        response = invoke_deepseek(
            messages=messages,
            temperature=0.7,
            max_tokens=MAX_TOKENS,
        )

        return response
    
    except Exception as e:
        return f"Error generating plan: {str(e)}"

@mcp.tool()
async def generate_code(language: str, 
                       task: str, 
                       context: Optional[str] = None, 
                       comments: bool = True) -> str:
    """Generate code based on requirements.
    
    Args:
        language: Programming language
        task: Description of what the code should do
        context: Additional context or existing code (optional)
        comments: Whether to include comments in the code
    """
    try:
        # Prepare messages for DeepSeek
        messages = [
            {
                "role": "system",
                "content": [{"text":"You are an expert programmer. Your task is to generate high-quality, efficient, and well-structured code based on requirements. Follow best practices for the specified programming language."}]
            },
            {
                "role": "user",
                "content": [{"text":f"Please generate {language} code for the following task:\n\n{task}\n\n" + f'Additional context or existing code:\n```{language}\n{context}\n```\n\n' if context else '' + 'Please include detailed comments.' if comments else 'No need for extensive comments.'}]
            }
        ]

        # Invoke DeepSeek model
        response = invoke_deepseek(
            messages=messages,
            temperature=0.3,  # Lower temperature for code generation
            max_tokens=MAX_TOKENS,
        )

        return response
    
    except Exception as e:
        return f"Error generating code: {str(e)}"

@mcp.tool()
async def review_code(language: str, 
                     code: str, 
                     focus: Optional[List[str]] = None) -> str:
    """Review code and provide feedback.
    
    Args:
        language: Programming language
        code: Code to review
        focus: Areas to focus on (bugs, performance, security, style, architecture)
    """
    try:
        # Prepare messages for DeepSeek
        messages = [
            {
                "role": "system",
                "content": [{"text":"You are an expert code reviewer. Your task is to provide detailed, constructive feedback on code. Focus on identifying issues, suggesting improvements, and explaining your reasoning."}]
            },
            {
                "role": "user",
                "content": [{"text":f"Please review the following {language} code:\n\n```{language}\n{code}\n```\n\n" + f'Please focus on these aspects: {", ".join(focus)}' if focus else 'Please provide a comprehensive review.'}]
            }
        ]

        # Invoke DeepSeek model
        response = invoke_deepseek(
            messages=messages,
            temperature=0.5,
            max_tokens=MAX_TOKENS,
        )

        return response
    
    except Exception as e:
        return f"Error reviewing code: {str(e)}"

@mcp.tool()
async def explain_code(language: str, 
                      code: str, 
                      detail_level: str = "intermediate") -> str:
    """Explain code in detail.
    
    Args:
        language: Programming language
        code: Code to explain
        detail_level: Level of detail in the explanation (basic, intermediate, advanced)
    """
    try:
        # Prepare messages for DeepSeek
        messages = [
            {
                "role": "system",
                "content": [{"text":"You are an expert programmer and educator. Your task is to explain code clearly and accurately, adapting your explanation to the requested level of detail."}]
            },
            {
                "role": "user",
                "content": [{"text":f"Please explain the following {language} code at a {detail_level} level of detail:\n\n```{language}\n{code}\n```"}]
            }
        ]

        # Invoke DeepSeek model
        response = invoke_deepseek(
            messages=messages,
            temperature=0.5,
            max_tokens=MAX_TOKENS,
        )

        return response
    
    except Exception as e:
        return f"Error explaining code: {str(e)}"

@mcp.tool()
async def refactor_code(language: str, 
                       code: str, 
                       goals: List[str]) -> str:
    """Refactor code to improve quality.
    
    Args:
        language: Programming language
        code: Code to refactor
        goals: Refactoring goals (readability, performance, modularity, security, maintainability)
    """
    try:
        # Prepare messages for DeepSeek
        messages = [
            {
                "role": "system",
                "content": [{"text":"You are an expert programmer specializing in code refactoring. Your task is to improve code quality while maintaining functionality. Provide both the refactored code and an explanation of your changes."}]
            },
            {
                "role": "user",
                "content": [{"text":f"Please refactor the following {language} code to improve {', '.join(goals)}:\n\n```{language}\n{code}\n```\n\nProvide the refactored code and explain your changes."}]
            }
        ]

        # Invoke DeepSeek model
        response = invoke_deepseek(
            messages=messages,
            temperature=0.4,
            max_tokens=MAX_TOKENS,
        )

        return response
    
    except Exception as e:
        return f"Error refactoring code: {str(e)}"

if __name__ == "__main__":
    # Check if AWS credentials are set
    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("AWS_SECRET_ACCESS_KEY"):
        print("AWS credentials are not set. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.")
        exit(1)
    
    # Run the server
    mcp.run(transport='stdio')
    
    # messages = [
    #     {
    #         "role": "system",
    #         "content": [{"text":"You are an expert project planner. Your task is to create detailed, actionable project plans based on requirements. Be thorough, practical, and consider all aspects of project planning including timeline, resources, milestones, and potential challenges."}]
    #     },
    #     {
    #         "role": "user",
    #         "content": [{"text":f"Please create a detailed project plan for the following requirements:\n\n帮我制作一份司美格鲁肽的介绍，包括特色功能，适用范围，发展历史，价格，图文并茂，需要制作成精美的 HTML保存到本地目录. "}]
    #     }
    # ]

    # response = invoke_deepseek(
    #         messages=messages,
    #         temperature=0.5,
    #         max_tokens=MAX_TOKENS,
    #     )

    # print(response)