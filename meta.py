FRAMES = {}

class Property(object):
    pass

class MetaFrame(type):
    def __new__(cls, name, bases, dict):
        t = type.__new__(cls, name, bases, dict)
        props = {}
        for name, p in dict.items():
            if isinstance(p, Property):
                props[name] = p
        t.props = props
        FRAMES[t.__name__] = t
        return t


class IntProperty(Property):
    pass


class Frame(object):
    __metaclass__ = MetaFrame
    name = 'this class'


class B(Frame):
    name = 'another'
    myvar = IntProperty()
    foo = IntProperty()


class C(B):
    __metaclass__ = type
    name = 'third'

print B.props
