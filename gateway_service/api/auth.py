import json
import os
import time
import urllib.request

import jwt
from django.http import JsonResponse
from jwt.algorithms import RSAAlgorithm


AUTH0_ISSUER = os.getenv(
    "AUTH0_ISSUER",
    "https://dev-5o8igifch4ha6z4p.us.auth0.com/"
)

AUTH0_AUDIENCE = os.getenv(
    "AUTH0_AUDIENCE",
    "https://car-rental-api"
)

AUTH0_JWKS_URI = os.getenv(
    "AUTH0_JWKS_URI",
    "https://dev-5o8igifch4ha6z4p.us.auth0.com/.well-known/jwks.json"
)

_jwks_cache = None
_jwks_cache_time = 0


def get_jwks():
    global _jwks_cache, _jwks_cache_time

    now = time.time()

    if _jwks_cache and now - _jwks_cache_time < 3600:
        return _jwks_cache

    with urllib.request.urlopen(AUTH0_JWKS_URI, timeout=5) as response:
        _jwks_cache = json.loads(response.read().decode("utf-8"))
        _jwks_cache_time = now
        return _jwks_cache


def get_token_from_header(request):
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    parts = auth_header.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


def validate_token(token):
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    jwks = get_jwks()

    rsa_key = None
    for key in jwks["keys"]:
        if key["kid"] == kid:
            rsa_key = RSAAlgorithm.from_jwk(json.dumps(key))
            break

    if rsa_key is None:
        raise Exception("Unable to find appropriate key")

    return jwt.decode(
        token,
        rsa_key,
        algorithms=["RS256"],
        audience=AUTH0_AUDIENCE,
        issuer=AUTH0_ISSUER,
    )


class JwtAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if not path.startswith("/api/"):
            return self.get_response(request)

        if path in ["/api/v1/authorize", "/api/v1/callback"]:
            return self.get_response(request)

        token = get_token_from_header(request)

        if not token:
            return JsonResponse({"message": "Unauthorized"}, status=401)

        try:
            payload = validate_token(token)
        except Exception as e:
            print("JWT validation error:", str(e))
            return JsonResponse({"message": "Unauthorized"}, status=401)

        request.jwt_payload = payload
        request.jwt_user = payload.get("email") or payload.get("sub")

        return self.get_response(request)