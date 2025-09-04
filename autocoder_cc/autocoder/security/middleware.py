"""security.middleware – common FastAPI security middlewares."""

from fastapi import FastAPI
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.sessions import SessionMiddleware

__all__ = ["apply_security_middleware"]


def apply_security_middleware(app: FastAPI, enable_https_redirect: bool = True) -> None:
    """Attach common security middleware to the FastAPI *app*.

    Parameters
    ----------
    app: FastAPI
        The application to mutate.
    enable_https_redirect: bool, default True
        Add HTTPSRedirectMiddleware which sends 307 redirects for http→https.
    """
    if enable_https_redirect:
        app.add_middleware(HTTPSRedirectMiddleware)

    # Example session middleware – could be used for CSRF tokens later.
    # app.add_middleware(SessionMiddleware, secret_key="replace-me") 