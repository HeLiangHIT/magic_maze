#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2023-01-17 22:38:10
# @Author  : HeLiang (helianghit@foxmail.com)
# @Link    : https://github.com/HeLiangHIT
# 此处r主要是为了支持在 doctest 命令中使用 \n
r'''
路径搜索，提供bfs(最短路)和dfs两种方法，入参相同，使用示例如下:
>>> m = Map((3, 3)); m.data[1][1] = Point.Wall; m.data[0][0] = Point.Start; m.data[1][2] = Point.End
>>> paths = bfs(m.data, [(0, 0),], [(1, 2),], callback=lambda m: print('\n'.join(["-----", ] + [' '.join([p.name[0] for p in row]) for row in m]))) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
-----
V C C
C W E
C C C
-----
V N C
V W E
C C C
...
V W N
V V C
-----
V V V
V W V
V V N
>>> print(paths) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[[(0, 0), (0, 1), (0, 2), (1, 2)]]

>>> paths = dfs(m.data, [(0, 0),], [(1, 2),], callback=lambda m: print('\n'.join(["-----", ] + [' '.join([p.name[0] for p in row]) for row in m]))) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
-----
V C C
C W E
C C C
-----
V C C
V W E
...
V V V
-----
V C C
V W V
V V V
>>> print(paths) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[[(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)]]
>>> paths = a_star(m.data, [(0, 0),], [(1, 2),], callback=lambda m: print('\n'.join(["-----", ] + [' '.join([p.name[0] for p in row]) for row in m]))) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
-----
V C C
C W E
C C C
-----
V V C
...
V V V
N W V
C C C
>>> print(paths) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
[[(0, 0), (0, 1), (0, 2), (1, 2)]]
'''
import sys
import os
import copy
import traceback
from queue import PriorityQueue
from .map import Point, Map


def _valid_check(mdata, srcs, targets):
    '''输入有效性检查'''
    if not (isinstance(mdata, list) and isinstance(mdata[0], list)):
        print(f"input parameter mdata is illegal(must be 2-dimension): {mdata}")
        traceback.print_stack()
        return False
    if not all([isinstance(p, Point) for row in mdata for p in row]): # 所有成员都是 Point 子类
        print(f"input parameter mdata is illegal(must be all Point type): {mdata}")
        traceback.print_stack()
        return False
    if not (isinstance(srcs, list) and isinstance(srcs[0], tuple) and isinstance(srcs[0][0], int)):
        print(f"input parameter srcs is illegal(must be list of coordinate): {srcs}")
        traceback.print_stack()
        return False
    if not (isinstance(targets, list) and isinstance(targets[0], tuple) and isinstance(targets[0][0], int)):
        print(f"input parameter targets is illegal(must be list of coordinate): {targets}")
        traceback.print_stack()
        return False
    # TODO: srcs/targets 是否超过边界
    return True


def _backtrace(pre_points, srcs, cur):
    '''回溯从srcs到cur的路径'''
    path = [cur, ]
    if cur not in pre_points: # 当前点(目标点)和起始点重复的特殊情况
        path.append(cur)
        return path[::-1]
    while pre_points[cur] not in srcs: # 遍历找到从源到当前点的路径
        cur = pre_points[cur]
        path.append(cur)
    path.append(pre_points[cur])
    return path[::-1]


def bfs(mdata, srcs, targets, max_steps = 20000, max_paths = 1, callback = None):
    r'''
    多点对多点的BFS最短路算法
    NOTE: mdata 为二维数组，入参 srcs 和 targets 需为数组实际下标； callback 为每次迭代计算的回调，用于实时在视图中刷新访问情况
    '''
    if not _valid_check(mdata, srcs, targets):
        return []
    width = len(mdata[0]) # 注意数组的保存是从上到下、从左到右
    height = len(mdata)
    _mdata = copy.deepcopy(mdata) # 避免直接修改实参
    
    q = srcs[:] # 待探索的点，避免直接修改实参
    avaliable_paths = [] # 可达结果路径列表
    targets_set = set(targets) # 避免目标重复和直接修改实参

    steps = 0 # 计算次数，避免超时
    pre_points = {} # 前序索引，用于回溯

    while q and targets_set:
        cur, *q = q
        steps += 1
        _mdata[cur[0]][cur[1]] = Point.Visited
        if callback is not None:
            callback(_mdata)
        if cur in targets_set: # 找到目标
            avaliable_paths.append(_backtrace(pre_points, srcs, cur)) # 保存最短路径
            # targets_set.remove(cur) # 移除目标，此处无需移除，允许下一条路径到达该目标
        else: # 非目标节点，增加相邻的合法节点
            udlr = [(cur[0] - 1, cur[1]), (cur[0] + 1, cur[1]), (cur[0], cur[1] - 1), (cur[0], cur[1] + 1),]
            qadd = [p for p in udlr if 0 <= p[0] < height and 0 <= p[1] < width and _mdata[p[0]][p[1]] in (Point.Chan, Point.End)] # NOTE: 终点也可选
            for p in qadd: # 记录目标点是从当前位置过去的
                _mdata[p[0]][p[1]] = Point.NxtVisit # 已经走过，设置即将访问的点避免再次被加入访问队列
                if p not in pre_points: # 增加标记前进路线，避免重复增加
                    pre_points[p] = cur
            q.extend(qadd)
        if len(avaliable_paths) >= max_paths:
            break
        if steps >= max_steps:
            break
    return avaliable_paths


def _dfs(mdata, cur, targets, iter_status, max_steps, max_paths, callback):
    width = len(mdata[0]) # 注意数组的保存是从上到下、从左到右
    height = len(mdata)

    pre = mdata[cur[0]][cur[1]]
    mdata[cur[0]][cur[1]] = Point.Visited
    iter_status["steps"] += 1
    iter_status["cur_path"].append(cur)

    # 边界条件
    if len(iter_status["avaliable_paths"]) >= max_paths or iter_status["steps"] >= max_steps:
        return False
    if callback is not None:
        callback(mdata)
    if cur in targets:
        iter_status["avaliable_paths"].append(iter_status["cur_path"][:])
        return True

    udlr = [(cur[0] - 1, cur[1]), (cur[0] + 1, cur[1]), (cur[0], cur[1] - 1), (cur[0], cur[1] + 1),]
    qadd = [p for p in udlr if 0 <= p[0] < height and 0 <= p[1] < width and mdata[p[0]][p[1]] in (Point.Chan, Point.End)]
    for p in qadd:
        _dfs(mdata, p, targets, iter_status, max_steps, max_paths, callback)

    iter_status["cur_path"].remove(cur)
    mdata[cur[0]][cur[1]] = pre


def dfs(mdata, srcs, targets, max_steps = 50000, max_paths = 1, callback = None):
    '''
    多点对多点的DFS最短路算法
    NOTE: mdata 为二维数组，入参 srcs 和 targets 需为数组实际下标； callback 为每次迭代计算的回调，用于实时在视图中刷新访问情况
    '''
    pre_stack_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(10000)
    if not _valid_check(mdata, srcs, targets):
        return []
    _mdata = copy.deepcopy(mdata) # 避免直接修改实参
    iter_status = {"steps": 0, # 访问步数
                   "cur_path": [], # 当前访问路径
                   "avaliable_paths": [], # 可达结果路径列表
                  }

    for p in srcs:
        _dfs(_mdata, p, targets, iter_status, max_steps, max_paths, callback)

    sys.setrecursionlimit(pre_stack_limit)
    return iter_status["avaliable_paths"]


def _calc_cost(cur, targets):
    # 计算当前点到目标点的最短距离
    dist = [abs(cur[0] - p[0]) + abs(cur[1] - p[1]) for p in targets]
    return min(dist)

def a_star(mdata, srcs, targets, max_steps = 50000, max_paths = 1, callback = None):
    '''
    多点对多点的A*最短路算法 -> BFS 算法改进为以距离优先出
    NOTE: mdata 为二维数组，入参 srcs 和 targets 需为数组实际下标； callback 为每次迭代计算的回调，用于实时在视图中刷新访问情况
    '''
    if not _valid_check(mdata, srcs, targets):
        return []
    width = len(mdata[0]) # 注意数组的保存是从上到下、从左到右
    height = len(mdata)
    _mdata = copy.deepcopy(mdata) # 避免直接修改实参
    
    q = PriorityQueue() # put by (priority_number, data) and lowest priority retrieved first
    for p in srcs:
        q.put((0, p))
    avaliable_paths = [] # 可达结果路径列表
    targets_set = set(targets) # 避免目标重复和直接修改实参

    steps = 0 # 计算次数，避免超时
    pre_points = {} # 前序索引，用于回溯

    while not q.empty() and targets_set: # 注意 q == True
        _, cur = q.get()
        steps += 1
        _mdata[cur[0]][cur[1]] = Point.Visited
        if callback is not None:
            callback(_mdata)
        if cur in targets_set: # 找到目标
            avaliable_paths.append(_backtrace(pre_points, srcs, cur)) # 保存最短路径
            # targets_set.remove(cur) # 移除目标，此处无需移除，允许下一条路径到达该目标
        else: # 非目标节点，增加相邻的合法节点
            udlr = [(cur[0] - 1, cur[1]), (cur[0] + 1, cur[1]), (cur[0], cur[1] - 1), (cur[0], cur[1] + 1),]
            qadd = [p for p in udlr if 0 <= p[0] < height and 0 <= p[1] < width and _mdata[p[0]][p[1]] in (Point.Chan, Point.End)] # NOTE: 终点也可选
            # NOTE: A* 算法和BFS算法的主要差异点就在这里
            for p in qadd: # 记录目标点是从当前位置过去的
                q.put((_calc_cost(p, targets), p))
                _mdata[p[0]][p[1]] = Point.NxtVisit # 已经走过，设置即将访问的点避免再次被加入访问队列
                if p not in pre_points: # 增加标记前进路线，避免重复增加
                    pre_points[p] = cur
        if len(avaliable_paths) >= max_paths:
            break
        if steps >= max_steps:
            break
    return avaliable_paths



if __name__ == '__main__':
    import doctest
    doctest.testmod()  # verbose=True shows the output

    # m = Map((15, 20), default = Point.Wall)
    # m.data[0][0] = Point.Start
    # m.data[0][1] = Point.Chan
    # m.data[14][19] = Point.End
    # answers = a_star(m.data, [(0, 0),], [(14, 19),])
    # print(answers)

    # data = [[Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall], 
    #         [Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall], 
    #         [Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Chan, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Chan, Point.Chan, Point.Wall], 
    #         [Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Chan, Point.Wall], 
    #         [Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Wall, Point.Chan, Point.Wall], 
    #         [Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Wall], 
    #         [Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Chan, Point.Chan, Point.Chan, Point.Wall, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Wall], 
    #         [Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall], 
    #         [Point.Wall, Point.Wall, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Wall, Point.Chan, Point.Chan, Point.Chan, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall], 
    #         [Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall], 
    #         [Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall], 
    #         [Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall], 
    #         [Point.Chan, Point.Chan, Point.Chan, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Wall, Point.Wall, Point.Wall], 
    #         [Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Wall, Point.Wall, Point.Wall], 
    #         [Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Chan, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Wall, Point.Chan, Point.Chan, Point.Chan, Point.Chan]
    #     ]
    # start = (0, 0)
    # end = (14, 19)
    # ans = bfs(data, [start, ], [end, ])
    # print(ans)
