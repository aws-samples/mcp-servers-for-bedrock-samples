import requests
import json
import base64
import os
from flask import Flask, request, redirect, url_for, session
from urllib.parse import urlencode
import secrets
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()
def load_config_from_env():
    """
    从环境变量中加载 OAuth 配置
    """
    # 默认配置
    config = {
        "REGION": "us-east-1",  # 默认 AWS 区域
        "DOMAIN": "",  # 默认 Cognito 域前缀
        "PUBLIC_CLIENT_ID": "",  # 公共客户端ID
        "PUBLIC_CLIENT_SECRET": "",  # 公共客户端密钥
        "CONFIDENTIAL_CLIENT_ID": "",  # M2M客户端ID
        "CONFIDENTIAL_CLIENT_SECRET": "",  # M2M客户端密钥
        "REDIRECT_URI": "",  # 默认回调URL
        "LOGOUT_URI": ""  # 默认注销URL
    }
    
    # 从环境变量更新配置
    for key in config.keys():
        env_value = os.getenv(key)
        if env_value:
            config[key] = env_value
    
    # 添加额外的环境变量（如果存在）
    user_pool_id = os.getenv("USER_POOL_ID")
    if user_pool_id:
        config["USER_POOL_ID"] = user_pool_id
    
    # 构建一些派生的URL
    config["COGNITO_DOMAIN"] = f"https://{config['DOMAIN']}.auth.{config['REGION']}.amazoncognito.com"
    config["AUTHORIZATION_ENDPOINT"] = f"{config['COGNITO_DOMAIN']}/oauth2/authorize"
    config["TOKEN_ENDPOINT"] = f"{config['COGNITO_DOMAIN']}/oauth2/token"
    config["USERINFO_ENDPOINT"] = f"{config['COGNITO_DOMAIN']}/oauth2/userInfo"
    config["LOGOUT_ENDPOINT"] = f"{config['COGNITO_DOMAIN']}/logout"

    return config

CONFIG = load_config_from_env()
print(f"Loaded OAuth configuration:{CONFIG}")

# 构建 Cognito URL
COGNITO_BASE_URL = f"https://{CONFIG['DOMAIN']}.auth.{CONFIG['REGION']}.amazoncognito.com"
COGNITO_AUTHORIZE_URL = f"{COGNITO_BASE_URL}/oauth2/authorize"
COGNITO_TOKEN_URL = f"{COGNITO_BASE_URL}/oauth2/token"
COGNITO_USERINFO_URL = f"{COGNITO_BASE_URL}/oauth2/userInfo"
COGNITO_LOGOUT_URL = f"{COGNITO_BASE_URL}/logout"

# 初始化 Flask 应用
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # 用于 session 加密

@app.route("/")
def index():
    return '''
    <h1>Cognito OAuth 客户端演示</h1>
    <a href="/login">使用 Amazon Cognito 登录</a><br>
    <a href="/m2m-demo">机器对机器 API 访问演示</a>
    '''

@app.route("/login")
def login():
    # 生成随机状态防止CSRF攻击
    state = secrets.token_hex(16)
    session['oauth_state'] = state

    print(f"登录时设置的 state: {state}")
    print(f"当前 session 内容: {session}")
    
    # 构建授权URL
    auth_params = {
        'response_type': 'code',
        'client_id': CONFIG['PUBLIC_CLIENT_ID'],
        'redirect_uri': CONFIG['REDIRECT_URI'],
        'state': state,
        'scope': 'openid email profile my-api/read'
    }
    auth_url = f"{COGNITO_AUTHORIZE_URL}?{urlencode(auth_params)}"
    
    # 重定向用户到认证端点
    return redirect(auth_url)

@app.route("/callback")
def callback():
    received_state = request.args.get('state')
    session_state = session.get('oauth_state')
    
    print(f"回调收到的 state: {received_state}")
    print(f"会话中存储的 state: {session_state}")
    print(f"当前 session 内容: {session}")
    
    # 验证状态防止CSRF攻击
    if received_state != session_state:
        return f"状态不匹配，可能存在CSRF攻击。收到: {received_state}，期望: {session_state}", 403
    
    
    # 获取授权码
    code = request.args.get('code')
    if not code:
        return "未收到授权码", 400
    
    # 使用授权码换取令牌
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': CONFIG['PUBLIC_CLIENT_ID'],
        'client_secret': CONFIG['PUBLIC_CLIENT_SECRET'],
        'code': code,
        'redirect_uri': CONFIG['REDIRECT_URI']
    }
    
    response = requests.post(COGNITO_TOKEN_URL, data=token_data)
    
    if response.status_code != 200:
        return f"获取令牌失败: {response.text}", 400
    
    # 保存令牌
    tokens = response.json()
    session['access_token'] = tokens.get('access_token')
    session['id_token'] = tokens.get('id_token')
    session['refresh_token'] = tokens.get('refresh_token')
    
    return redirect(url_for('profile'))

@app.route("/profile")
def profile():
    # 检查是否已认证
    access_token = session.get('access_token')
    id_token = session.get('id_token')
    if not access_token:
        return redirect(url_for('login'))
    
    # 使用访问令牌获取用户信息
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(COGNITO_USERINFO_URL, headers=headers)
    
    if response.status_code != 200:
        return f"获取用户信息失败: {response.text}", 400
    
    user_info = response.json()
    
    # 构建个人资料页面
    profile_html = f'''
    <h1>用户资料</h1>
    <p>邮箱: {user_info.get('email', 'N/A')}</p>
    <p>名称: {user_info.get('name', 'N/A')}</p>
    <p>用户ID: {user_info.get('sub', 'N/A')}</p>
    <hr>
    <h3>用户信息</h3>
    <pre>{json.dumps(user_info, indent=4)}</pre>
    <hr>
    <h3>访问令牌</h3>
    <pre>{access_token}</pre>
    <hr>
    <h3>ID令牌</h3>
    <pre>{id_token}</pre>
    <hr>
    <a href="/logout">退出登录</a>
    '''
    
    return profile_html

@app.route("/logout")
def logout():
    # 构建注销URL
    logout_params = {
        'client_id': CONFIG['PUBLIC_CLIENT_ID'],
        'logout_uri': CONFIG['LOGOUT_URI']
    }
    
    # 清除本地会话
    session.clear()
    
    # 重定向到Cognito的注销端点
    logout_url = f"{COGNITO_LOGOUT_URL}?{urlencode(logout_params)}"
    return redirect(logout_url)

@app.route("/logout-callback")
def logout_callback():
    return '''
    <h1>已成功注销</h1>
    <a href="/">返回首页</a>
    '''

@app.route("/m2m-demo")
def m2m_demo():
    try:
        # 获取客户端凭证令牌
        token = get_m2m_token()
        
        # 使用令牌调用API示例
        result = call_api_with_token(token)
        
        return f'''
        <h1>机器对机器 API 访问演示</h1>
        <h2>成功获取令牌:</h2>
        <pre>{json.dumps(token, indent=4)}</pre>
        
        <h2>API 调用结果:</h2>
        <pre>{json.dumps(result, indent=4)}</pre>
        
        <a href="/">返回首页</a>
        '''
    except Exception as e:
        return f'''
        <h1>机器对机器 API 访问演示</h1>
        <h2>错误:</h2>
        <pre>{str(e)}</pre>
        <a href="/">返回首页</a>
        '''

def get_m2m_token():
    """获取机器对机器OAuth令牌"""
    client_id = CONFIG['CONFIDENTIAL_CLIENT_ID']
    client_secret = CONFIG['CONFIDENTIAL_CLIENT_SECRET']
    
    # 构建基本认证头
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode('utf-8')).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'client_credentials',
        'scope': 'my-api/read my-api/write'
    }
    
    response = requests.post(COGNITO_TOKEN_URL, headers=headers, data=data)
    
    if response.status_code != 200:
        raise Exception(f"获取令牌失败: {response.text}")
    
    return response.json()

def call_api_with_token(token):
    """使用令牌调用示例API"""
    # 在实际应用中替换为您的真实API端点
    return {
        "success": True,
        "message": "成功使用M2M令牌进行API调用",
        "token_type": token.get("token_type"),
        "expires_in": token.get("expires_in"),
        "scope": token.get("scope")
    }

if __name__ == "__main__":
    app.run(debug=True, port=5000)