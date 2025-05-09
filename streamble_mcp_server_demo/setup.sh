#!/bin/bash

# 设置默认值
REGION=${AWS_REGION:-us-east-1}
DOMAIN_PREFIX="mcp-server-oauth-domain"
APP_URL=${APP_URL:-"http://localhost:5000"}  # 注意这里使用 localhost 而不是 127.0.0.1

echo "使用AWS配置中的区域: $REGION"
echo "使用默认应用URL: $APP_URL"

# 创建 Cognito 用户池
echo "Creating Cognito User Pool..."
USER_POOL_ID=$(aws cognito-idp create-user-pool \
  --pool-name "MyAppUserPool" \
  --auto-verified-attributes email \
  --schema Name=email,Required=true,Mutable=true \
  --mfa-configuration OFF \
  --query 'UserPool.Id' \
  --output text)

echo "User Pool created with ID: $USER_POOL_ID"

# 设置 Cognito 域
echo "Setting up Cognito domain..."
aws cognito-idp create-user-pool-domain \
  --user-pool-id $USER_POOL_ID \
  --domain $DOMAIN_PREFIX

echo "Domain created: https://$DOMAIN_PREFIX.auth.$REGION.amazoncognito.com"

# 创建资源服务器
echo "Creating Resource Server..."
aws cognito-idp create-resource-server \
  --user-pool-id $USER_POOL_ID \
  --identifier "my-api" \
  --name "My API Server" \
  --scopes ScopeName=read,ScopeDescription="Read access to API" \
          ScopeName=write,ScopeDescription="Write access to API"

echo "Resource Server created with identifier: my-api"

# 公共客户端（用于浏览器/移动应用）
echo "Creating Public App Client..."
PUBLIC_CLIENT=$(aws cognito-idp create-user-pool-client \
  --user-pool-id $USER_POOL_ID \
  --client-name "MyPublicAppClient" \
  --generate-secret \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --allowed-o-auth-flows code implicit \
  --allowed-o-auth-scopes openid email profile my-api/read \
  --callback-urls "$APP_URL/callback" \
  --logout-urls "$APP_URL/logout" \
  --supported-identity-providers COGNITO \
  --prevent-user-existence-errors ENABLED \
  --allowed-o-auth-flows-user-pool-client)

PUBLIC_CLIENT_ID=$(echo $PUBLIC_CLIENT | jq -r '.UserPoolClient.ClientId')
PUBLIC_CLIENT_SECRET=$(echo $PUBLIC_CLIENT | jq -r '.UserPoolClient.ClientSecret')

echo "Public App Client created with ID: $PUBLIC_CLIENT_ID"
echo "Public Client Secret: $PUBLIC_CLIENT_SECRET"

# 机密客户端（用于服务器到服务器）
echo "Creating Confidential App Client (M2M)..."
CONFIDENTIAL_CLIENT=$(aws cognito-idp create-user-pool-client \
  --user-pool-id $USER_POOL_ID \
  --client-name "MyConfidentialClient" \
  --generate-secret \
  --explicit-auth-flows ALLOW_REFRESH_TOKEN_AUTH \
  --allowed-o-auth-flows client_credentials \
  --allowed-o-auth-scopes my-api/read my-api/write \
  --supported-identity-providers COGNITO \
  --prevent-user-existence-errors ENABLED)

CONFIDENTIAL_CLIENT_ID=$(echo $CONFIDENTIAL_CLIENT | jq -r '.UserPoolClient.ClientId')
CONFIDENTIAL_CLIENT_SECRET=$(echo $CONFIDENTIAL_CLIENT | jq -r '.UserPoolClient.ClientSecret')

echo "Confidential App Client created with ID: $CONFIDENTIAL_CLIENT_ID"
echo "Client Secret: $CONFIDENTIAL_CLIENT_SECRET"

# 写入环境变量到.env文件
echo "Writing configuration to .env file..."
cat > .env << EOF
REGION=$REGION
DOMAIN=$DOMAIN_PREFIX
USER_POOL_ID=$USER_POOL_ID
PUBLIC_CLIENT_ID=$PUBLIC_CLIENT_ID
PUBLIC_CLIENT_SECRET=$PUBLIC_CLIENT_SECRET
CONFIDENTIAL_CLIENT_ID=$CONFIDENTIAL_CLIENT_ID
CONFIDENTIAL_CLIENT_SECRET=$CONFIDENTIAL_CLIENT_SECRET
REDIRECT_URI=$APP_URL/callback
LOGOUT_URI=$APP_URL/logout
EOF

echo "Environment variables written to .env file"
echo "OAuth Server Provider setup complete!"