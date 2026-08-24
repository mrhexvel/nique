from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar, cast

from nique.shared.di.scope import Scope
from nique.shared.exceptions import DependencyResolutionError

T = TypeVar("T")
Factory = Callable[["Container"], object]


@dataclass(frozen=True, slots=True)
class _Provider:
    factory: Factory
    scope: Scope


class Container:
    """Small hierarchical DI container used only by composition roots."""

    def __init__(self, scope: Scope, parent: Container | None = None) -> None:
        self.scope = scope
        self._parent = parent
        self._providers: dict[type[object], _Provider] = {}
        self._instances: dict[type[object], object] = {}

    def register_instance(self, contract: type[T], instance: T) -> None:
        self._instances[contract] = instance

    def register(self, contract: type[T], factory: Callable[[Container], T], scope: Scope) -> None:
        self._providers[contract] = _Provider(factory, scope)

    def child(self, scope: Scope) -> Container:
        return Container(scope, parent=self)

    def resolve(self, contract: type[T]) -> T:
        owner = self._find_owner(contract)
        if owner is None:
            raise DependencyResolutionError(f"No provider registered for {contract.__name__}")
        if contract in owner._instances:
            return cast("T", owner._instances[contract])
        provider = owner._providers[contract]
        target = self._scope_owner(provider.scope)
        if target is None:
            raise DependencyResolutionError(
                f"{contract.__name__} requires unavailable {provider.scope.value} scope"
            )
        instance = provider.factory(self)
        target._instances[contract] = instance
        return cast("T", instance)

    def _find_owner(self, contract: type[object]) -> Container | None:
        current: Container | None = self
        while current is not None:
            if contract in current._instances or contract in current._providers:
                return current
            current = current._parent
        return None

    def _scope_owner(self, scope: Scope) -> Container | None:
        current: Container | None = self
        while current is not None:
            if current.scope is scope:
                return current
            current = current._parent
        return None
