from typing import Protocol


class LikeDuck(Protocol):
    a: int = 2
    b: str

    def quack(self):
        ...

    def walk(self):
        ...


class Chicken:
    def __init__(self) -> None:
        self.a = 2
        self.b = '3'

    def quack(self):
        print('quack in SMY')

    def walk(self):
        print('walk')


chick: LikeDuck = Chicken()
