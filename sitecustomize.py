# Compatibility shim for older libraries expecting inspect.getargspec
import inspect
from collections import namedtuple

if not hasattr(inspect, 'getargspec'):
    try:
        getfullargspec = inspect.getfullargspec
    except AttributeError:
        # Fallback: define a minimal getfullargspec-like behavior
        def getfullargspec(func):
            return namedtuple('FullArgSpec', 'args varargs varkw defaults')([], None, None, None)

    def getargspec(func):
        fas = getfullargspec(func)
        ArgSpec = namedtuple('ArgSpec', 'args varargs keywords defaults')
        return ArgSpec(args=fas.args, varargs=fas.varargs, keywords=getattr(fas, 'varkw', None), defaults=fas.defaults)

    inspect.getargspec = getargspec
