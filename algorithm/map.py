#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2023-01-17 21:55:38
# @Author  : HeLiang (helianghit@foxmail.com)
# @Link    : https://github.com/HeLiangHIT

'''
迷宫算法涉及的基本数据结构，包括Point和Map，使用示例:
>>> m = Map(); print(m) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
10X10:
C C C C C C C C C C
    ...
>>> m.data[1][1] = Point.Wall
>>> m.data = Point.Wall # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
Traceback (most recent call last):
    ...
AttributeError: can't set attribute 'data'
>>> print(m) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
10X10:
C C C C C C C C C C
C W C C C C C C C C
    ...
>>> m.save("./empty.map")
>>> m1 = Map.load("./empty.map")
>>> print(m1) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
10X10:
C C C C C C C C C C
C W C C C C C C C C
    ...
>>> os.remove("./empty.map")
>>> m1.data[0][0] = Point.Start;m1.data[9][9] = Point.End;print(Map().diff(m1))
[(0, 0, <Point.Start: 3>), (1, 1, <Point.Wall: 2>), (9, 9, <Point.End: 4>)]
>>> print(m1.start, m1.end)
[(0, 0)] [(9, 9)]
>>> txt = m1.to_json(); print(txt)
{"data": [[3, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 2, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1, 1, 1, 4]]}
>>> m2, isok = Map().from_json(txt); print(m2) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
10X10:
S C C C C C C C C C
C W C C C C C C C C
...
'''
import os
import pickle
import json
import copy
from enum import IntEnum


Point = IntEnum('Point', ('Chan', 'Wall', 'Start', 'End', "Visited", "NxtVisit")) # Enum is not JSON serializable


class Map(object):
    '''地图对象: 支持创建、修改成员、保存、加载'''
    def __init__(self, size = (10, 10), default = Point.Chan, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._size = size
        self._data = [[default for _ in range(self._size[1])] for _ in range(self._size[0])]

    def __str__(self):
        # mtx = '\n'.join([' '.join([f"{p.value}" for p in row]) for row in self._data])
        mtx = '\n'.join([' '.join([p.name[0] for p in row]) for row in self._data])
        return f"{self._size[1]}X{self._size[0]}:\n{mtx}"

    def from_data(self, data):
        self._size = (len(data), len(data[0]))
        self._data = copy.deepcopy(data)
        return self

    def diff(self, other): # different from __sub__ witch return Map
        # 计算差异: [(x, y, other_value), ...]
        res = []
        if self._size != other.size:
            print(f"Map diff with different size: {self.size} != {other.size}")
            return res
        for m in range(self._size[0]):
            for n in range(self._size[1]):
                if self._data[m][n] != other.data[m][n]:
                    res.append((m, n, other.data[m][n]))
        return res

    @property # avoid modify data use m.data = Point.Wall, can use as m.data[1][1] = Point.Wall
    def data(self):
        return self._data

    @property
    def size(self):
        return self._size

    @property
    def start(self):
        res = []
        for m in range(self._size[0]):
            for n in range(self._size[1]):
                if self._data[m][n] == Point.Start:
                    res.append((m, n))
        return res

    @property
    def end(self):
        res = []
        for m in range(self._size[0]):
            for n in range(self._size[1]):
                if self._data[m][n] == Point.End:
                    res.append((m, n))
        return res

    def save(self, path):
        with open(path, "wb") as f:
            s = pickle.dumps(self)
            f.write(s)

    @staticmethod
    def load(path):
        with open(path, "rb") as f:
            s = f.read()
            m = pickle.loads(s)
            return m

    def to_json(self):
        txt = json.dumps({
            "data": self._data
            })
        return txt

    @staticmethod
    def from_json(txt):
        dic = json.loads(txt)
        values = tuple(item.value for item in Point) # 用于校验
        if not all([p in values for row in dic["data"] for p in row]): # 确保所有值都是有效Point
            print(f"json value is not valid Point: {dic['data']}")
            return None, False
        data = [[Point(p) for p in row] for row in dic["data"]]
        return Map().from_data(data), True


if __name__ == '__main__':
    import doctest
    doctest.testmod()  # verbose=True shows the output