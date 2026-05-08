from vk_collector.clients.vk_api import EXECUTE_BATCH_LIMIT, _build_execute_code


def test_execute_code_single():
    code = _build_execute_code(["ria"], count=50)
    assert 'API.wall.get({"domain": "ria", "count": 50})' in code
    assert code.startswith("return [")
    assert code.endswith("];")


def test_execute_code_multiple():
    code = _build_execute_code(["ria", "tass", "rbc"], count=25)
    assert code.count("API.wall.get") == 3
    assert '"domain": "tass"' in code
    assert '"count": 25' in code


def test_execute_batch_limit_is_25():
    assert EXECUTE_BATCH_LIMIT == 25
