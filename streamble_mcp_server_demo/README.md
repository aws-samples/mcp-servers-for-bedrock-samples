# AWS Cognito 作为 OAuth Provider 实现的 Streamable MCP Server

本项目演示如何使用 AWS Cognito 作为 OAuth 提供者，实现一个带有身份验证的 Streamable MCP Server。

## 1. 设置 AWS Cognito

### 1.1 先决条件
- 需要安装 AWS CLI 以及配置好 AWS credentials

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
bash setup.sh us-east-1 https://<实际ip>:<port>
```

## 2. 项目结构

```
streamble_mcp_server_demo/
├── .env                  # 环境变量配置
├── main.py               # MCP 客户端示例（支持 Cognito 认证）
├── pyproject.toml        # 项目依赖
├── README.md             # 项目说明
├── setup.sh              # Cognito 设置脚本
└── src/
    ├── auth.py           # Flask 应用示例（用于展示 Cognito OAuth 流程）
    ├── cognito_auth.py   # Cognito 认证工具类
    └── server.py         # 带有 Cognito 认证的 MCP 服务器
```

## 3. 依赖安装

使用 Python 包管理器安装依赖：

```bash
pip install -e .
# 或者
uv install
```

## 4. 运行服务器

启动带有 Cognito 认证的 MCP 服务器：

```bash
python src/server.py
```

服务器将在 `http://localhost:8080` 启动，并要求所有 MCP 请求提供有效的 Cognito 访问令牌。

## 5. 测试客户端

使用客户端测试 MCP 服务器，自动获取 M2M 令牌：

```bash
python main.py
```

使用自定义令牌：

```bash
python main.py --token <您的访问令牌>
```

## 6. 认证流程实现

### 6.1 机器对机器认证 (M2M)

我们使用 Cognito 客户端凭证流程实现 M2M 认证：

1. 通过 `cognito_auth.py` 中的 `CognitoAuthenticator` 类获取 M2M 令牌
2. 使用 JWT 标准验证令牌
3. 向 MCP 服务器发出请求时在请求头中使用 Bearer 令牌

### 6.2 令牌验证

服务器端验证流程：

1. FastAPI 中间件拦截所有 MCP 请求
2. 提取并验证 Authorization 头中的 Bearer 令牌
3. 使用 Cognito JWKS（JSON Web Key Set）验证令牌签名和有效期
4. 验证成功后，允许请求继续处理

## 7. MCP 服务功能

本示例实现了一个简单的计算器 MCP 服务器，提供以下工具：

- add: 两数相加
- subtract: 相减
- multiply: 相乘
- divide: 相除
- power: 乘方运算
- square_root: 平方根计算

所有工具都需要通过有效的 Cognito 认证才能访问。

## 8. 安全注意事项

- 保护 .env 文件中的客户端密钥
- 在生产环境中使用 HTTPS
- 定期轮换客户端密钥
- 使用适当的 CORS 配置
- 根据最小特权原则为不同用户分配权限范围
- 验证令牌时检查权限范围、有效期和签名