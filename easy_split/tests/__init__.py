# -*- coding: utf-8 -*-
import os, types, unittest

# Import all Python test cases in this tests directory
for filename in os.listdir(os.path.dirname(__file__)):
    if (filename[-3:] == ".py" and
        filename != "__init__.py" and
        filename[0] != '.'):
        module = __import__('.'.join((__name__, filename[:-3])), (), (), ["*"])
        for name in dir(module):
            function = getattr(module, name)
            if (type(function) is types.TypeType and
                issubclass(function, unittest.TestCase)):
                globals()[name] = function
