def print_hello_world() -> str:
    return "hello world"


def test_print_hello_world():
    expected = "hello world"
    actual = print_hello_world()
    assert expected == actual, "Function did not print 'hello world'"
