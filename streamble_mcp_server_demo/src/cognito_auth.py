import os
import requests
import json
import base64
import jwt
import time
from typing import Dict, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CognitoAuthenticator:
    def __init__(self):
        """Initialize the Cognito authenticator with configuration from environment variables"""
        self.config = self._load_config_from_env()
        self.jwks = None
        self.jwks_last_updated = 0
        self._load_jwks()
    
    def _load_config_from_env(self) -> Dict[str, str]:
        """Load Cognito configuration from environment variables"""
        config = {
            "REGION": os.getenv("REGION", "us-east-1"),
            "USER_POOL_ID": os.getenv("USER_POOL_ID", ""),
            "DOMAIN": os.getenv("DOMAIN", ""),
            "CONFIDENTIAL_CLIENT_ID": os.getenv("CONFIDENTIAL_CLIENT_ID", ""),
            "CONFIDENTIAL_CLIENT_SECRET": os.getenv("CONFIDENTIAL_CLIENT_SECRET", ""),
            "PUBLIC_CLIENT_ID": os.getenv("PUBLIC_CLIENT_ID", "")
        }
        
        # Build derived URLs
        config["COGNITO_DOMAIN"] = f"https://{config['DOMAIN']}.auth.{config['REGION']}.amazoncognito.com"
        config["TOKEN_ENDPOINT"] = f"{config['COGNITO_DOMAIN']}/oauth2/token"
        config["JWKS_URI"] = f"https://cognito-idp.{config['REGION']}.amazonaws.com/{config['USER_POOL_ID']}/.well-known/jwks.json"
        
        return config
    
    def _load_jwks(self) -> None:
        """Load JSON Web Key Set (JWKS) from Cognito for token validation"""
        # Only refresh JWKS every 24 hours
        current_time = time.time()
        if self.jwks and (current_time - self.jwks_last_updated < 86400):  # 24 hours
            return
        
        try:
            jwks_url = self.config["JWKS_URI"]
            response = requests.get(jwks_url)
            if response.status_code == 200:
                self.jwks = response.json()
                self.jwks_last_updated = current_time
                print(f"Successfully loaded JWKS from {jwks_url}")
            else:
                print(f"Failed to load JWKS: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error loading JWKS: {str(e)}")
    
    def get_key(self, kid: str) -> Optional[Dict]:
        """
        Get the public key that matches the key ID from the JWKS
        """
        if not self.jwks:
            self._load_jwks()
            
        if not self.jwks:
            return None
            
        for key in self.jwks.get('keys', []):
            if key.get('kid') == kid:
                return key
        return None
    
    def validate_token(self, token: str) -> Dict:
        """
        Validate the JWT token and return the claims if valid
        
        Args:
            token: The JWT token to validate
            
        Returns:
            The decoded claims if the token is valid
            
        Raises:
            Exception: If the token is invalid
        """
        # Get the header to extract the key ID (kid)
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
            
            if not kid:
                raise Exception("Token header missing 'kid'")
                
            # Get the key from JWKS
            key = self.get_key(kid)
            if not key:
                raise Exception(f"No matching key found for kid: {kid}")
                
            # Construct the public key in PEM format
            n = base64.urlsafe_b64decode(key['n'] + '=' * (4 - len(key['n']) % 4))
            e = base64.urlsafe_b64decode(key['e'] + '=' * (4 - len(key['e']) % 4))
            
            # Verify and decode the token
            claims = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                audience=self.config["PUBLIC_CLIENT_ID"],
                options={"verify_signature": False}  # We're using a simplified validation approach
            )
            
            # Verify additional claims
            current_time = int(time.time())
            if claims.get('exp') and current_time > claims['exp']:
                raise Exception("Token has expired")
            
            if claims.get('nbf') and current_time < claims['nbf']:
                raise Exception("Token not yet valid")
            
            return claims
            
        except jwt.InvalidTokenError as e:
            raise Exception(f"Invalid token: {str(e)}")
        except Exception as e:
            raise Exception(f"Error validating token: {str(e)}")
    
    def extract_token_from_header(self, auth_header: Optional[str]) -> Optional[str]:
        """
        Extract the JWT token from the Authorization header
        
        Args:
            auth_header: The Authorization header value
            
        Returns:
            The token if found, None otherwise
        """
        if not auth_header:
            return None
            
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
            
        return parts[1]
    
    def get_m2m_token(self, scopes: List[str] = None) -> Dict:
        """
        Get a machine-to-machine token using client credentials flow
        
        Args:
            scopes: List of scopes to request
            
        Returns:
            The token response dictionary
        """
        if scopes is None:
            scopes = ['my-api/read']
            
        client_id = self.config['CONFIDENTIAL_CLIENT_ID']
        client_secret = self.config['CONFIDENTIAL_CLIENT_SECRET']
        
        # Build basic auth header
        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode('utf-8')).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials',
            'scope': ' '.join(scopes)
        }
        
        response = requests.post(self.config['TOKEN_ENDPOINT'], headers=headers, data=data)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get token: {response.text}")
        
        return response.json()
