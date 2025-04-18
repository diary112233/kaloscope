from functools import wraps
from inspect import isawaitable


def request_ctx(ctx: dict):
    """Sets the context for the request.

    Args:
        ctx: The context to set.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            for key, value in ctx.items():
                setattr(request.ctx, key, value)
            response = func(request, *args, **kwargs)
            if isawaitable(response):
                response = await response
            return response

        return wrapper

    return decorator


def before(method: str):
    """Decorator to execute a method before the main method is called.

    Args:
        method: The method to execute.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            getattr(self, method)()
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


def after(method: str):
    """Decorator to execute a method after the main method returns.

    Args:
        method: The method to execute.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            getattr(self, method)()
            return result

        return wrapper

    return decorator
