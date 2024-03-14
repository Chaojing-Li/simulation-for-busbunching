
class A:
    def __init__(self, a) -> None:
        self.a = a

    def __repr__(self) -> str:
        return str(self.a)


data = {0: [A(0), A(1)], 1: [A(2)], 2: [A(3)]}

second_queue = data[1]

second_queue.pop(0)

