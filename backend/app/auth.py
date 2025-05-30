import os
import jwt
from datetime import datetime, timedelta
from typing import Optional
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings
from ninja.security import HttpBearer


class JWTAuth(HttpBearer):
    """JWT Authentication for Django Ninja"""

    def authenticate(self, request, token):
        if not token or not token.strip():
            return None

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            if not user_id:
                return None

            try:
                user = User.objects.get(id=user_id, is_active=True)
                request.user = user
                return user
            except User.DoesNotExist:
                return None

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            # Catch any other unexpected errors
            return None


def generate_tokens(user: User) -> dict:
    """Generate access and refresh tokens for a user"""
    if not user or not user.is_active:
        raise ValueError("Invalid user for token generation")

    # Access token expires in 1 hour
    access_payload = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "type": "access",
    }

    # Refresh token expires in 7 days
    refresh_payload = {
        "user_id": user.id,
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow(),
        "type": "refresh",
    }

    try:
        access_token = jwt.encode(
            access_payload, settings.SECRET_KEY, algorithm="HS256"
        )
        refresh_token = jwt.encode(
            refresh_payload, settings.SECRET_KEY, algorithm="HS256"
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
        }
    except Exception as e:
        raise ValueError(f"Token generation failed: {str(e)}")


def verify_refresh_token(token: str) -> Optional[User]:
    """Verify refresh token and return user if valid"""
    if not token or not token.strip():
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        if payload.get("type") != "refresh":
            return None

        user_id = payload.get("user_id")
        if not user_id:
            return None

        return User.objects.get(id=user_id, is_active=True)

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist):
        return None
    except Exception:
        # Catch any other unexpected errors
        return None


# Initialize JWT auth instance
jwt_auth = JWTAuth()
