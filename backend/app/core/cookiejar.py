import time
from http.cookiejar import Cookie, CookieJar
from multiprocessing.synchronize import RLock

from sanic import Sanic

from app.models.general import GlobalCookie


class SQLiteCookieJar(CookieJar):
    """SQLite-backed cookie jar."""

    def __init__(self, app: Sanic, policy=None):
        super().__init__(policy)
        self._cookies: dict = app.shared_ctx.cookies  # DictProxy
        self._cookies_lock: RLock = app.shared_ctx.cookies_lock

    def set_cookie(self, cookie):
        """Set a cookie, without checking whether or not it should be set."""
        c = self._cookies
        self._cookies_lock.acquire()
        try:
            if cookie.domain not in c:
                c[cookie.domain] = {}
            c2 = c[cookie.domain]
            if cookie.path not in c2:
                c2[cookie.path] = {}
            c3 = c2[cookie.path]
            c3[cookie.name] = cookie
            # update nested dict
            c[cookie.domain] = c2
        finally:
            self._cookies_lock.release()

    def get_cookie(self, domain, path=None, name=None):
        """Get a cookie by domain, path and name."""
        c2 = self._cookies.get(domain)
        if not c2:
            return None

        now = time.time()

        # check if the cookie is expired
        def not_expired(cookie):
            return cookie.expires is None or cookie.expires >= now

        if path is not None and path in c2:
            c3 = c2[path]
            if name is not None and name in c3:
                cookie = c3[name]
                if not_expired(cookie):
                    return cookie
            elif name is None:
                for cookie in c3.values():
                    if not_expired(cookie):
                        return cookie
        elif path is None:
            for c3 in c2.values():
                for cookie in c3.values():
                    if not_expired(cookie):
                        return cookie

    def clear(self, domain=None, path=None, name=None):
        """Clear some cookies.

        Invoking this method without arguments will clear all cookies.  If
        given a single argument, only cookies belonging to that domain will be
        removed.  If given two arguments, cookies belonging to the specified
        path within that domain are removed.  If given three arguments, then
        the cookie with the specified name, path and domain is removed.

        Raises KeyError if no matching cookie exists.

        """
        if name is not None:
            if (domain is None) or (path is None):
                raise ValueError(
                    "domain and path must be given to remove a cookie by name"
                )
            c2 = self._cookies[domain]
            del c2[path][name]
            # update nested dict
            self._cookies[domain] = c2
        elif path is not None:
            if domain is None:
                raise ValueError("domain must be given to remove cookies by path")
            c2 = self._cookies[domain]
            del c2[path]
            # update nested dict
            self._cookies[domain] = c2
        elif domain is not None:
            del self._cookies[domain]
        else:
            self._cookies.clear()

    async def load(self):
        """Load cookies from the database."""
        if self._cookies_lock.acquire(block=False):
            try:
                now = time.time()
                await GlobalCookie.filter(expires__lt=now).delete()
                cookies = await GlobalCookie.filter(expires__gte=now)
                for cookie in cookies:
                    self.set_cookie(
                        Cookie(
                            version=0,
                            name=cookie.name,
                            value=cookie.value,
                            port=None,
                            port_specified=False,
                            domain=cookie.domain,
                            domain_specified=bool(cookie.domain),
                            domain_initial_dot=cookie.domain.startswith("."),
                            path=cookie.path,
                            path_specified=bool(cookie.path),
                            secure=False,
                            expires=cookie.expires,
                            discard=False,
                            comment=None,
                            comment_url=None,
                            rest={},
                            rfc2109=False,
                        )
                    )
            finally:
                self._cookies_lock.release()

    async def save(self):
        """Save cookies to database."""
        if self._cookies_lock.acquire(block=False):
            try:
                now = time.time()
                for cookie in self:
                    if cookie.discard or cookie.expires is None or cookie.expires < now:
                        continue
                    _cookie = await GlobalCookie.get_or_none(
                        name=cookie.name,
                        domain=cookie.domain,
                        path=cookie.path,
                    )
                    if _cookie is not None:
                        await GlobalCookie.filter(id=_cookie.id).update(
                            value=cookie.value,
                            expires=cookie.expires,
                        )
                    else:
                        await GlobalCookie.create(
                            name=cookie.name,
                            value=cookie.value,
                            domain=cookie.domain,
                            path=cookie.path,
                            expires=cookie.expires,
                        )
            finally:
                self._cookies_lock.release()
