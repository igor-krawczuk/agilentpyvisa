class DummyTester():

    def __init__(self, *args,**kwargs):
        pass

    def query(*args, **kwargs):
        print(*[x for x in args if isinstance(x, str)])
        if kwargs:
            print(kwargs)
        if any(("UNT" in x for x in args if type(x)is str)):
            return ";".join(["B1517A,0"]*5)
        elif any(("LRN" in x for x in args if type(x)is str)):
            return "CL1;"
        else:
            return "+0"

    def write(*args, **kwargs):
        print(*[x for x in args if isinstance(x, str)])
        if kwargs:
            print(kwargs)
