#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2023-01-18 16:50:55
# @Author  : HeLiang (helianghit@foxmail.com)
# @Link    : https://github.com/HeLiangHIT
# @Ref     : https://blog.csdn.net/juzihongle1/article/details/73135920 和 https://www.cnblogs.com/shiroe/p/15506909.html
#            还有递归分割等很多迷宮生成算法
# 此处r主要是为了支持在 doctest 命令中使用 \n
r'''
迷宫生成，提供dfsg(深度优先)和primg(随机广度)两种方法，入参相同，使用示例如下:
>>> callback = lambda m: print('\n'.join(["-----", ] + [' '.join([p.name[0] for p in row]) for row in m]))
>>> m = dfsg((3, 3), [(0, 0),], [(2, 2),], callback=callback) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
-----
C W W
...
...C
>>> print(m) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
3X3:
S...
...
...E
>>> m = primg((3, 3), [(0, 0),], [(2, 2),], callback=callback) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
-----
C W W
...
...C
>>> print(m) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
3X3:
S...
...
...E
>>> m = dfsg((6, 6), [(0, 0),], [(5, 5),], callback=callback) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
-----
C...
...
...W
>>> print(m) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
6X6:
S...
...
...E
>>> m = primg((60, 60), [(0, 0),], [(45, 51),]) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
>>> print(m) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
60X60:
S...
...
W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W W
'''
import sys
import copy
import random
import traceback
from functools import reduce
from .map import Point, Map


def _valid_check(size, starts, ends):
    '''输入有效性检查'''
    if not (isinstance(starts, list) and isinstance(starts[0], tuple) and isinstance(starts[0][0], int)):
        print(f"input parameter starts is illegal(must be list of coordinate): {starts}")
        traceback.print_stack()
        return False
    if not (isinstance(ends, list) and isinstance(ends[0], tuple) and isinstance(ends[0][0], int)):
        print(f"input parameter ends is illegal(must be list of coordinate): {ends}")
        traceback.print_stack()
        return False
    # TODO: srcs/targets 是否超过边界
    return True


def _valid_neighbour(m, cur, value = Point.Wall):
    size = m.size
    udlr = [(cur[0] - 1, cur[1]), (cur[0] + 1, cur[1]), (cur[0], cur[1] - 1), (cur[0], cur[1] + 1),]
    unvisited_nb = reduce(lambda x, y: x + y, [0 <= q[0] < size[0] and 0 <= q[1] < size[1] and m.data[q[0]][q[1]] == value for q in udlr])
    return unvisited_nb


def _connect_points(m, targets):
    for p in targets:
        if _valid_neighbour(m, p, Point.Chan) == 0:
            udlr = [(p[0] - 1, p[1]), (p[0] + 1, p[1]), (p[0], p[1] - 1), (p[0], p[1] + 1),]
            ava_nb = filter(lambda x: _valid_neighbour(m, x, Point.Chan) >= 1, udlr)
            link = random.choice(list(ava_nb))
            m.data[link[0]][link[1]] = Point.Chan
    return m


def dfsg(size, starts, ends, callback = None):
    '''深度优先迷宫生成算法:
    算法流程:
    1.将起点作为当前迷宫单元并标记为已访问
    2.当还存在未标记的迷宫单元，进行循环
        1.如果当前迷宫单元有未被访问过的相邻的迷宫单元
            1.随机选择一个未访问的相邻迷宫单元
            2.将当前迷宫单元入栈
            3.移除当前迷宫单元与相邻迷宫单元的墙
            4.标记相邻迷宫单元并用它作为当前迷宫单元
        2.如果当前迷宫单元不存在未访问的相邻迷宫单元，并且栈不空
            1.栈顶的迷宫单元出栈
            2.令其成为当前迷宫单元
    这种算法生成的迷宫会有比较明显的主路
    '''
    if not _valid_check(size, starts, ends):
        return []
    pre_stack_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(10000)
    m = Map(size, default = Point.Wall)
    visited_flag = [[False for _ in range(size[1])] for _ in range(size[0])]

    def dfs(cur):
        visited_flag[cur[0]][cur[1]] = True
        m.data[cur[0]][cur[1]] = Point.Chan

        if callback is not None:
            callback(m.data)

        if cur in ends: # 走到终点就不用打通终点周围的墙了
            return
        udlr = [(cur[0] - 2, cur[1]), (cur[0] + 2, cur[1]), (cur[0], cur[1] - 2), (cur[0], cur[1] + 2),]
        random.shuffle(udlr)
        for p in udlr:
            if 0 <= p[0] < size[0] and 0 <= p[1] < size[1] and not visited_flag[p[0]][p[1]] and _valid_neighbour(m, p) >= 1:
                if cur[0] == p[0]:
                    m.data[p[0]][min(cur[1], p[1]) + 1] = Point.Chan
                    visited_flag[p[0]][min(cur[1], p[1]) + 1] = True
                else:
                    m.data[min(cur[0], p[0]) + 1][p[1]] = Point.Chan
                    visited_flag[min(cur[0], p[0]) + 1][p[1]] = True
                dfs(p)

    dfs(starts[0]) # DFS 只需要一条线走到黑
    # start[0] 和 starts[1:]/end 之间差非偶数的情况下无法联通，需要链接终点到最近的可行点
    m = _connect_points(m, starts[1:] + ends)

    for p in starts:
        m.data[p[0]][p[1]] = Point.Start
    for p in ends:
        m.data[p[0]][p[1]] = Point.End
    sys.setrecursionlimit(pre_stack_limit)
    return m


def primg(size, starts, ends, callback = None):
    '''随机Prim算法生成迷宫 - 更像随机广度优先算法
    1.让迷宫全是墙
    2.选一个单元格作为迷宫的通路，然后把它的邻墙放入列表
    3.当列表里还有墙时
        1.从列表里随机选一个墙，如果这面墙分隔的两个单元格只有一个单元格被访问过
            1.那就从列表里移除这面墙，即把墙打通，让未访问的单元格成为迷宫的通路
            2.把这个格子的墙加入列表
        2.如果墙两面的单元格都已经被访问过，那就从列表里移除这面墙
    改进: 如果把墙放到列表中，比较复杂，维基里面提到了改进策略。可以维护一个迷宫单元格的列表，而不是边的列表。在这个迷宫单元格列表里面存放了未访问的单元格，我们在单元格列表中随机挑选一个单元格，如果这个单元格有多面墙联系着已存在的迷宫通路，我们就随机选择一面墙打通。
    相对于深度优先的算法，Prim随机算法不是优先选择最近选中的单元格，而是随机的从所有的列表中的单元格进行选择，新加入的单元格和旧加入的单元格同样概率会被选择，新加入的单元格没有有优先权。因此其分支更多，生成的迷宫更复杂，难度更大，也更自然。
    '''
    if not _valid_check(size, starts, ends):
        return []
    m = Map(size, default = Point.Wall)
    visited_flag = [[False for _ in range(size[1])] for _ in range(size[0])] # 防止还在队列里的被重复打通，则会存在环路

    queue = [[start, (-1, -1)] for start in starts] # 当前点，前一个点
    while queue:
        cur, pre = queue.pop(random.randint(0, len(queue) - 1))
        if _valid_neighbour(m, cur) < 1:
            continue
        m.data[cur[0]][cur[1]] = Point.Chan
        visited_flag[cur[0]][cur[1]] = True

        if pre[0] != -1 and cur[0] == pre[0]:
            m.data[cur[0]][min(cur[1], pre[1]) + 1] = Point.Chan
        elif pre[1] != -1 and cur[1] == pre[1]:
            m.data[min(cur[0], pre[0]) + 1][cur[1]] = Point.Chan

        if callback is not None:
            callback(m.data)

        udlr = [(cur[0] - 2, cur[1]), (cur[0] + 2, cur[1]), (cur[0], cur[1] - 2), (cur[0], cur[1] + 2),]
        random.shuffle(udlr)
        for p in udlr:
            if 0 <= p[0] < size[0] and 0 <= p[1] < size[1] and m.data[p[0]][p[1]] == Point.Wall and not visited_flag[p[0]][p[1]]:
                queue.append([p, cur])
                visited_flag[p[0]][p[1]] = True # 目标点已经追加过

    # start 和 end 之间差非偶数的情况下无法联通，需要链接终点到最近的可行点
    m = _connect_points(m, ends)

    for p in starts:
        m.data[p[0]][p[1]] = Point.Start
    for p in ends:
        m.data[p[0]][p[1]] = Point.End
    return m


def kruskalg(size, starts, ends, callback = None):
    '''随机Kruskal算法 (并查集)
    1.创建所有墙的列表（除了四边），并且创建所有单元的集合，每个集合中只包含一个单元。
    2.随机从墙的列表中选取一个，取该墙两边分隔的两个单元
        1.两个单元属于不同的集合，则将去除当前的墙，把分隔的两个单元连同当前墙三个点作为一个单元集合；并将当前选中的墙移出列表
        2.如果属于同一个集合，则直接将当前选中的墙移出列表
    3.不断重复第 2 步，直到所有墙都检测过
    该算法同样不会出现明显的主路，岔路也比较多
    Pyhthon 实现可以参考(代码太难看): https://blog.csdn.net/cj12345657582255/article/details/115605195
    '''
    m = Map(size, default = Point.Wall)
    print("Unrelized method kruskalg")
    traceback.print_stack()
    for p in starts:
        m.data[p[0]][p[1]] = Point.Start
    for p in ends:
        m.data[p[0]][p[1]] = Point.End
    return m


if __name__ == '__main__':
    import doctest
    doctest.testmod()  # verbose=True shows the output
    
    # generate = primg # dfsg, primg, kruskalg
    # callback = lambda m: print('\n'.join(["-----", ] + [' '.join([p.name[0] for p in row]) for row in m]))
    # m = generate((3, 3), [(0, 0),], [(2, 2),], callback=callback)
    # print(m)
    # m = generate((6, 6), [(0, 0),], [(5, 5),], callback=callback)
    # print(m)
    # m = generate((60, 60), [(0, 0),], [(45, 51),])
    # print(m)