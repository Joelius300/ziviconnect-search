import requests


def bake_cookies(raw_cookie: str):
    return dict(cookie.split("=", 1) for cookie in raw_cookie.split("; "))


def auth_session(bearer_token: str, raw_cookie: str):
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {bearer_token}"
    s.headers.update(
        {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-zivi-locale": "de-CH",
        }
    )
    s.cookies.update(bake_cookies(raw_cookie))

    return s
