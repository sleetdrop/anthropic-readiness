"""Offline tests may connect only to disposable loopback services."""

import ipaddress
import socket

import pytest


@pytest.fixture(autouse=True)
def prohibit_external_connections(monkeypatch: pytest.MonkeyPatch) -> None:
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex

    def check(sock: socket.socket, address: str | tuple[object, ...]) -> None:
        if sock.family in {socket.AF_INET, socket.AF_INET6}:
            host = str(address[0]) if isinstance(address, tuple) else address
            try:
                allowed = ipaddress.ip_address(host).is_loopback
            except ValueError:
                allowed = host == "localhost"
            if not allowed:
                raise RuntimeError("external_network_forbidden_in_offline_tests")

    def guarded_connect(sock: socket.socket, address: str | tuple[object, ...]) -> None:
        check(sock, address)
        connect(sock, address)

    def guarded_connect_ex(sock: socket.socket, address: str | tuple[object, ...]) -> int:
        check(sock, address)
        return connect_ex(sock, address)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
