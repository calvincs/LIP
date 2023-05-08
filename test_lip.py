import pytest
import os
import time
from lip import LIPModule, LIPClient


@LIPModule(lru=True)
def sum_func(a, b):
    return a + b


@LIPModule(lru=True)
def product_func(a, b):
    return a * b

@pytest.fixture(scope="module")
def servers():
    s1 = sum_func(init=True)
    s2 = product_func(init=True)
    yield
    s1.terminate()
    s2.terminate()


def test_lipmodule_init():
    lipmodule = LIPModule()
    assert lipmodule.log_level == 20
    assert lipmodule.lru is False
    assert lipmodule.lru_max is None


def test_lipclient_init():
    client = LIPClient()
    assert isinstance(client.sockets, dict)


def test_lipclient_scan_sockets():
    client = LIPClient()
    sockets = client.scan_sockets()
    assert isinstance(sockets, dict)
    assert "sum_func" in sockets
    assert "product_func" in sockets


def test_lipclient_refresh_sockets():
    client = LIPClient()
    client.refresh_sockets()
    assert "sum_func" in client.sockets
    assert "product_func" in client.sockets


def test_lipclient_get_docstring(servers):
    client = LIPClient()
    doc1 = client.get_docstring("sum_func")
    doc2 = client.get_docstring("product_func")

    assert doc1 is None
    assert doc2 is None


def test_lipclient_call_function(servers):
    client = LIPClient()

    result1 = client.call_function("sum_func", args=[3, 4])
    assert result1 == 7

    result2 = client.call_function("product_func", args=[3, 4])
    assert result2 == 12


def test_lipclient_list_functions(servers):
    client = LIPClient()
    functions = client.list_functions()
    assert "sum_func" in functions
    assert "product_func" in functions


def test_invalid_function_name(servers):
    client = LIPClient()

    with pytest.raises(ValueError, match="Function 'non_existent_function' not found in available sockets."):
        client.call_function("non_existent_function", args=[1, 2])


def test_invalid_arguments(servers):
    client = LIPClient()

    with pytest.raises(ValueError, match="missing a required argument: 'b'"):
        client.call_function("sum_func", args=[1])


if __name__ == "__main__":
    pytest.main([__file__])
