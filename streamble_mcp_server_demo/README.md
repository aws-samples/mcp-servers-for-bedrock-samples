# AWS Cognito 作为 OAuth Provider 实现的 Streamable MCP Server

本项目演示如何使用 AWS Cognito 作为 OAuth 提供者，实现一个带有身份验证的 Streamable MCP Server。

## 1. 设置 AWS Cognito

### 1.1 先决条件
- 需要安装 AWS CLI 以及配置好 AWS credentials
- 安装 jq
```bash
sudo apt update
# Install jq
sudo apt install -y jq
# Verify the installation
jq --version
```

### 1.2 修改并执行 Cognito 设置脚本
#### 解释：
1. **创建用户池：**
   - 创建一个具有密码策略和邮箱验证的用户池
   - 定义基本用户属性架构

2. **配置域名：**
   - 为 OAuth 端点设置 Cognito 托管域名
   - 格式为：https://myapp-oauth-domain.auth.[region].amazoncognito.com

3. **创建资源服务器：**
   - 定义一个名为 "my-api" 的资源服务器，具有自定义权限范围 "read" 和 "write"
   - 这些权限范围将以 my-api/read 和 my-api/write 的形式提供

4. **创建应用客户端：**
   - 面向网页/移动应用的公共客户端：
     - 生成客户端密钥
     - 授权码和隐式流程
     - 可访问 OpenID 权限范围和读取权限
   - 面向机器对机器(M2M)的私密客户端：
     - 生成客户端密钥
     - 客户端凭证授权类型
     - 可访问读取和写入权限

#### 执行设置脚本
根据实际情况修改后，执行如下命令：
```bash
bash setup.sh us-east-1 https://<实际ip>:3000
```

## 2. 项目结构

```
streamble_mcp_server_demo/
├── .env                  # 环境变量配置
├── main.py               # 简单的客户端示例
├── pyproject.toml        # 项目依赖
├── README.md             # 项目说明
├── setup.sh              # Cognito 设置脚本
└── src/
    ├── auth.py           # Cognito OAuth 认证流程
    ├── client.py         # MCP 客户端测试代码
    ├── cognito_auth_server.py  # 带 Cognito 认证的 MCP 服务器
    └── server.py         # 基础 MCP 服务器
```

## 3. 运行服务器

启动带有 Cognito 认证的 MCP 服务器：

```bash
python src/cognito_auth_server.py
```

## 4. 测试客户端

使用客户端测试 MCP 服务器：

```bash
python src/client.py
```

## 5. 认证流程

1. **机器对机器认证 (M2M)**：
   - 使用客户端凭证流程获取访问令牌
   - 在请求头中使用 Bearer 令牌访问 MCP 服务器

2. **用户认证**：
   - 通过 Cognito 托管 UI 进行用户登录
   - 获取访问令牌和 ID 令牌
   - 使用访问令牌调用 MCP 服务器

## 6. 安全注意事项

- 保护 .env 文件中的客户端密钥
- 在生产环境中使用 HTTPS
- 定期轮换客户端密钥
- 为不同的应用场景设置适当的权限范围
