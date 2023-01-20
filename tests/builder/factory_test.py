from __future__ import annotations

import pytest

from twister2.builder.factory import BuilderFactory


def test_if_get_builder_method_raises_KeyError_exception_when_there_is_no_register_builder():
    with pytest.raises(KeyError):
        BuilderFactory.get_builder('do_not_exist')


def test_if_create_instance_method_can_create_new_class_instance():
    class MyClass:
        def __init__(self, a, b):
            self.a = a
            self.b = b

    BuilderFactory.register_builder_class('my_class', MyClass)  # type: ignore
    my_class = BuilderFactory.create_instance('my_class', 1, b=2)
    assert my_class.a == 1  # type: ignore
    assert my_class.b == 2  # type: ignore
