from typing import List


class Bus():
    def __init__(self, id: int):
        self._id = id


class Stop():
    def __init__(self, buses: List[Bus]):
        self._buses = buses


if __name__ == '__main__':
    stop = Stop([1.0, 2.0, 3.0])
    print(stop._buses)
