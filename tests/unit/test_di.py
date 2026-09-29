from __future__ import annotations

from nique.shared.di import Container, Scope


class Service:
    pass


def test_scoped_singletons_are_isolated() -> None:
    app = Container(Scope.APPLICATION)
    app.register(Service, lambda _container: Service(), Scope.ACCOUNT)
    first = app.child(Scope.ACCOUNT)
    second = app.child(Scope.ACCOUNT)

    assert first.resolve(Service) is first.resolve(Service)
    assert first.resolve(Service) is not second.resolve(Service)
