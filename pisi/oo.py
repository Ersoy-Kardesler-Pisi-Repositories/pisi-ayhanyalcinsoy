# -*- coding: utf-8 -*-

# Guido's cool metaclass examples. fair use. ahahah.
# I find these quite handy. Use them :)

class autoprop(type):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        props = {}
        for name in dct.keys():
            if name.startswith("_get_") or name.startswith("_set_"):
                props[name[5:]] = 1
        for name in props.keys():
            fget = getattr(cls, f"_get_{name}", None)
            fset = getattr(cls, f"_set_{name}", None)
            setattr(cls, name, property(fget, fset))

class autosuper(type):
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        setattr(cls, f"_{name}__super", super(cls))

class autosuprop(autosuper, autoprop):
    pass

class autoeq(type):
    "useful for structures"
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        def equal(self, other):
            return self.__dict__ == other.__dict__
        cls.__eq__ = equal

class Struct(metaclass=autoeq):
    def __init__(self, **entries):
        self.__dict__.update(entries)
