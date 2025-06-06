from core.dispatcher import MessageHandler
from core.router import Router

# TODO: rewrite this module to a class-based implementation
_registered_routers: list[Router] = []


def load_router(router: Router) -> None:
    """
    Register a single router instance.
    """
    _registered_routers.append(router)


def load_routers(routers: list[Router]) -> None:
    """
    Register multiple router instances.
    """
    _registered_routers.extend(routers)


def get_all_handlers() -> list[MessageHandler]:
    """
    Aggregate all handlers from all registered routers.
    """
    handlers: list[MessageHandler] = []
    for router in _registered_routers:
        handlers.extend(router.get_handlers())
    return handlers


def get_all_routers() -> list[Router]:
    """
    Get a list of all registered routers.
    """
    return _registered_routers
