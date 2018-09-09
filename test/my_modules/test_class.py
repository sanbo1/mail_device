# -*- coding: utf-8 -*-

class TestClass(object):

    def __init__(self, **kwargs):
        if "test" in kwargs:
            print(test)

    def test_method(self):
        print("called test_method")

