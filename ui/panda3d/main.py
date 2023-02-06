#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2023-02-01 21:08:57
# @Author  : HeLiang (helianghit@foxmail.com)
# @Link    : https://github.com/HeLiangHIT
# @ref     : https://docs.panda3d.org/1.10/python/introduction/index
import sys
import os
import time
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import OnscreenText
from direct.gui.DirectSlider import DirectSlider
from direct.interval.IntervalGlobal import Sequence, Parallel
from panda3d.core import GeomVertexFormat, GeomVertexData, Geom, GeomTriangles, GeomVertexWriter, GeomNode, CardMaker
from panda3d.core import Texture, TextureStage, TextNode, WindowProperties
from panda3d.core import Light, Spotlight, PerspectiveLens, AmbientLight, DirectionalLight
from panda3d.core import LVector3, Point3
from direct.actor.Actor import Actor
from direct.task.Timer import Timer

from algorithm.map import Point, Map
from algorithm.generate import dfsg, primg
from algorithm.search import bfs, dfs, a_star


_script_dir = os.path.dirname(os.path.realpath(__file__))
win2unix_path = lambda p: "/" + p[0].lower() + "/" + p[1:].replace('\\', '/').replace(':', '') # Windows path to Unix-style path


class Cube(GeomNode):
    # 生成立方体
    def __init__(self, *args, **kwargs):
        super().__init__('Cube', *args, **kwargs)

        square0 = self.makeSquare(-1, -1, -1, 1, -1, 1)
        square1 = self.makeSquare(-1, 1, -1, 1, 1, 1)
        square2 = self.makeSquare(-1, 1, 1, 1, -1, 1)
        square3 = self.makeSquare(-1, 1, -1, 1, -1, -1)
        square4 = self.makeSquare(-1, -1, -1, -1, 1, 1)
        square5 = self.makeSquare(1, -1, -1, 1, 1, 1)

        self.addGeom(square0)
        self.addGeom(square1)
        self.addGeom(square2)
        self.addGeom(square3)
        self.addGeom(square4)
        self.addGeom(square5)

    @staticmethod
    def makeSquare(x1, y1, z1, x2, y2, z2):
        # helper function to make a square given the Lower-Left-Hand and Upper-Right-Hand corners
        fmt = GeomVertexFormat.getV3n3cpt2()
        vdata = GeomVertexData('Cube', fmt, Geom.UHDynamic)

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        texcoord = GeomVertexWriter(vdata, 'texcoord')

        # make sure we draw the sqaure in the right plane
        if x1 != x2:
            vertex.addData3(x1, y1, z1)
            vertex.addData3(x2, y1, z1)
            vertex.addData3(x2, y2, z2)
            vertex.addData3(x1, y2, z2)

            normal.addData3(Cube.normalized(2 * x1 - 1, 2 * y1 - 1, 2 * z1 - 1))
            normal.addData3(Cube.normalized(2 * x2 - 1, 2 * y1 - 1, 2 * z1 - 1))
            normal.addData3(Cube.normalized(2 * x2 - 1, 2 * y2 - 1, 2 * z2 - 1))
            normal.addData3(Cube.normalized(2 * x1 - 1, 2 * y2 - 1, 2 * z2 - 1))
        else:
            vertex.addData3(x1, y1, z1)
            vertex.addData3(x2, y2, z1)
            vertex.addData3(x2, y2, z2)
            vertex.addData3(x1, y1, z2)

            normal.addData3(Cube.normalized(2 * x1 - 1, 2 * y1 - 1, 2 * z1 - 1))
            normal.addData3(Cube.normalized(2 * x2 - 1, 2 * y2 - 1, 2 * z1 - 1))
            normal.addData3(Cube.normalized(2 * x2 - 1, 2 * y2 - 1, 2 * z2 - 1))
            normal.addData3(Cube.normalized(2 * x1 - 1, 2 * y1 - 1, 2 * z2 - 1))

        # adding different colors to the vertex for visibility
        color.addData4f(1.0, 1.0, 1.0, 1.0)
        color.addData4f(1.0, 1.0, 1.0, 1.0)
        color.addData4f(1.0, 1.0, 1.0, 1.0)
        color.addData4f(1.0, 1.0, 1.0, 1.0)

        texcoord.addData2f(0.0, 1.0)
        texcoord.addData2f(0.0, 0.0)
        texcoord.addData2f(1.0, 0.0)
        texcoord.addData2f(1.0, 1.0)

        # Quads aren't directly supported by the Geom interface
        # you might be interested in the CardMaker class if you are
        # interested in rectangle though
        tris = GeomTriangles(Geom.UHDynamic)
        tris.addVertices(0, 1, 3)
        tris.addVertices(1, 2, 3)

        square = Geom(vdata)
        square.addPrimitive(tris)
        return square

    @staticmethod
    def normalized(*args):
        # You can't normalize inline so this is a helper function
        myVec = LVector3(*args)
        myVec.normalize()
        return myVec


class Panda(Actor):
    def __init__(self, parent, *args, **kwargs):
        super().__init__("models/panda-model", {"walk": "models/panda-walk4"}, *args, **kwargs)
        self.reparentTo(parent)
        self.setScale(0.0012, 0.0012, 0.0012)
        self.setHpr(180, 0, 0)
        # self.loop("walk") # self.stop("walk")
        
    def up(self, relative = False, checker = None, interval = 0.5):
        # https://docs.panda3d.org/1.10/python/programming/models-and-actors/actor-animations
        # print(f"up with relative={relative}")
        curhpr, curpos = self.getHpr(), self.getPos()
        if relative:
            real_action = {Point3(180, 0, 0): self.up, Point3(270, 0, 0): self.left,
                           Point3(90, 0, 0): self.right, Point3(0, 0, 0): self.down,}[curhpr]
            return real_action(False, checker)
        tarhpr = Point3(180, 0, 0)
        nxtpos = curpos + Point3(0, 1, 0)
        if checker is not None and not checker(nxtpos):
            return Parallel()
        return Parallel(
            self.actorInterval("walk", loop = 0),
            self.hprInterval(interval / 5, tarhpr, startHpr = curhpr),
            self.posInterval(interval, nxtpos, startPos = curpos),
            )

    def left(self, relative = False, checker = None, interval = 0.5):
        # print(f"left with relative={relative}")
        curhpr, curpos = self.getHpr(), self.getPos()
        if relative:
            real_action = {Point3(180, 0, 0): self.left, Point3(270, 0, 0): self.down,
                           Point3(90, 0, 0): self.up, Point3(0, 0, 0): self.right,}[curhpr]
            return real_action(False, checker)
        tarhpr = Point3(270, 0, 0)
        nxtpos = curpos + Point3(-1, 0, 0)
        if checker is not None and not checker(nxtpos):
            return Parallel()
        return Parallel(
            self.actorInterval("walk", loop = 0),
            self.hprInterval(interval / 5, tarhpr, startHpr = curhpr),
            self.posInterval(interval, nxtpos, startPos = curpos),
            )

    def right(self, relative = False, checker = None, interval = 0.5):
        # print(f"right with relative={relative}")
        curhpr, curpos = self.getHpr(), self.getPos()
        if relative:
            real_action = {Point3(180, 0, 0): self.right, Point3(270, 0, 0): self.up,
                           Point3(90, 0, 0): self.down, Point3(0, 0, 0): self.left,}[curhpr]
            return real_action(False, checker)
        tarhpr = Point3(90, 0, 0)
        nxtpos = curpos + Point3(1, 0, 0)
        if checker is not None and not checker(nxtpos):
            return Parallel()
        return Parallel(
            self.actorInterval("walk", loop = 0),
            self.hprInterval(interval / 5, tarhpr, startHpr = curhpr),
            self.posInterval(interval, nxtpos, startPos = curpos),
            )

    def down(self, relative = False, checker = None, interval = 0.5):
        # print(f"down with relative={relative}")
        curhpr, curpos = self.getHpr(), self.getPos()
        if relative:
            real_action = {Point3(180, 0, 0): self.down, Point3(270, 0, 0): self.right,
                           Point3(90, 0, 0): self.left, Point3(0, 0, 0): self.up,}[curhpr]
            return real_action(False, checker)
        tarhpr = Point3(0, 0, 0)
        nxtpos = curpos + Point3(0, -1, 0)
        if checker is not None and not checker(nxtpos):
            return Parallel()
        return Parallel(
            self.actorInterval("walk", loop = 0),
            self.hprInterval(interval / 5, tarhpr, startHpr = curhpr),
            self.posInterval(interval, nxtpos, startPos = curpos),
            )


def load_ball(loader, parent):
    bamboo_texture = loader.loadTexture(win2unix_path(os.path.sep.join([_script_dir, "models", "bamboo_leaves.jpg"])))
    bamboo_texture.setWrapU(Texture.WM_mirror)
    bamboo_texture.setWrapV(Texture.WM_mirror)
    ball = loader.loadModel(win2unix_path(os.path.sep.join([_script_dir, "models", "ball.egg.pz"])))
    ts = TextureStage('ts')
    ts.setMode(TextureStage.MModulateGlow)
    # ts.setCombineAlpha(1, 1, 4) # https://docs.panda3d.org/1.10/python/reference/panda3d.core.TextureStage#panda3d.core.TextureStage
    ball.setTexPos(ts, 0, 0.6, 0.2) # https://docs.panda3d.org/1.10/python/programming/texturing/texture-transforms
    ball.setTexture(ts, bamboo_texture)
    ball.reparentTo(parent)
    return ball


class MyApp(ShowBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setBackgroundColor(0, 0, 0)
        props = WindowProperties( )
        props.setTitle('Magic Maze')
        # props.setIconFilename(win2unix_path(os.path.sep.join([_script_dir, "models", "maze.png"])))
        self.win.requestProperties(props)
        self.display_help()
        self.objs, self.lgts = [], []

        self.panda = Panda(self.render)
        self.ball = load_ball(self.loader, self.render)
        self.generate_maze()
        # https://docs.panda3d.org/1.10/python/programming/hardware-support/keyboard-support
        self.accept("0", lambda : (self.set_global_view, self.set_panda_view)[self.global_view]()) # 自动新迷宫
        self.accept("1", lambda : self.generate_maze()) # 生成新迷宫
        self.accept("2", lambda : self.auto_run_maze()) # 自动走迷宫
        self.accept("escape", sys.exit)

    def auto_run_maze(self):
        answers  = bfs(self.maze_map.data, [self.start, ], [self.end, ])
        class ActAnswer():
            def __init__(self, answer, actor, checker, interrupter, recover):
                self.answer = answer
                self.index = 1
                self.actor = actor
                self.checker = checker
                self.recover = recover # 禁用按键响应
                interrupter()
            def __next__(self):
                prepos = self.answer[self.index - 1]
                curpos = self.answer[self.index]
                self.index += 1
                delta = Point3(int(curpos[1] - prepos[1]), int(curpos[0] - prepos[0]), 0)
                act = {Point3(1, 0, 0): self.actor.up, Point3(-1, 0, 0): self.actor.down,
                       Point3(0, 1, 0): self.actor.right, Point3(0, -1, 0): self.actor.left,}[delta]
                if self.index < len(self.answer):
                    Timer().startCallback(0.2, lambda : self.__next__())
                else:
                    self.recover() # 恢复按键响应
                self.actor.setPos(prepos[0], prepos[1], 0)
                return act(checker = self.checker, interval = 0.1).start()
        def bankey(op):
            if op:
                self.accept("1", lambda : print("can't generate, please wait auto run finish"))
                self.accept("2", lambda : print("can't auto run again, please wait pre one finish"))
            else:
                self.accept("1", lambda : self.generate_maze())
                self.accept("2", lambda : self.auto_run_maze())
        gen = ActAnswer(answers[0], self.panda, self._check_conflict, lambda : bankey(True), lambda : bankey(False))
        Timer().startCallback(0.2, lambda : gen.__next__()) # call once

    def generate_maze(self):
        if self.objs:
            for cube in self.objs:
                cube.removeNode()
        if self.lgts:
            for lgt in self.lgts:
                self.render.setLightOff(lgt)
                lgt.removeNode()
        val = self.slider.guiItem.getValue()
        height = (10, 30, 50)[(val > 0.33) + (val > 0.66)] # 三个档小，中，大
        self.objs, self.lgts = [], []
        self.size, self.start, self.end = (height, height), (0, 0), (height - 1, height - 1)
        self.wall_texture = self.loader.loadTexture(win2unix_path(os.path.sep.join([_script_dir, "models", "limba.jpg"])))

        # 绘制地板和边缘
        self.add_floor_and_edge()

        # 绘制迷宫墙
        self.maze_map = primg(self.size, [self.start, ], [self.end, ])
        # print(self.maze_map)
        for m in range(self.maze_map.size[0]):
            for n in range(self.maze_map.size[1]):
                if self.maze_map.data[m][n] == Point.Wall:
                    self.add_cube(m, n)

        # 放置起点和终点
        self.panda.setPos(self.start[0], self.start[1], 0)
        self.ball.setPos(self.end[0], self.end[1], 0)

        # 放置摄像机 - 第三人称视角
        self.set_global_view()

        # 放置灯光
        self.add_lights(self.size[0] / 2, self.size[1] / 2)

    def set_global_view(self):
        # https://docs.panda3d.org/1.10/python/programming/camera-control/default-camera-driver
        #  Z-up coordinate system, we are looking at the +Y axis
        self.global_view = True
        self.disableMouse()
        x, y, z = self.size[0] / 2, self.size[1] / 2, (self.size[0] + self.size[1]) * 1.1
        self.camera.reparentTo(self.render)
        self.camera.setPosHpr(x, y, z, 0, 270, 0)
        self.accept("arrow_up", lambda : self.panda.up(False, self._check_conflict).start())
        self.accept("arrow_down", lambda : self.panda.down(False, self._check_conflict).start())
        self.accept("arrow_left", lambda : self.panda.left(False, self._check_conflict).start())
        self.accept("arrow_right", lambda : self.panda.right(False, self._check_conflict).start())

    def set_panda_view(self):
        self.global_view = False
        self.disableMouse()
        self.camera.reparentTo(self.panda)
        self.camera.setPos(0, 4000, 10000) # 熊猫尺寸较大
        self.camera.setHpr(0, 245, 180)
        self.accept("arrow_up", lambda : self.panda.up(True, self._check_conflict).start())
        self.accept("arrow_down", lambda : self.panda.down(True, self._check_conflict).start())
        self.accept("arrow_left", lambda : self.panda.left(True, self._check_conflict).start())
        self.accept("arrow_right", lambda : self.panda.right(True, self._check_conflict).start())

    def _check_conflict(self, pos):
        if round(pos.getX()) >= len(self.maze_map.data) or round(pos.getY()) >= len(self.maze_map.data[0]):
            return True
        if self.maze_map.data[round(pos.getX())][round(pos.getY())] != Point.Wall:
            return True
        return False

    def add_floor_and_edge(self):
        floor_texture = self.loader.loadTexture(win2unix_path(os.path.sep.join([_script_dir, "models", "iron05.jpg"])))
        floor = self.render.attachNewNode(Cube())
        ts = TextureStage('ts')
        ts.setMode(TextureStage.MModulate)
        floor.setTexScale(ts, 10, 10, 10)
        floor.setTexture(ts, floor_texture)
        floor.setTwoSided(True)
        floor.setScale(self.size[0], self.size[1], 0.1)
        floor.setPos(self.size[0] / 2, self.size[1] / 2, 0)
        self.objs.append(floor)
        for x in range(-1, self.size[0] + 1):
            self.add_cube(x, -1).setTexture(ts, floor_texture)
            self.add_cube(x, self.size[1]).setTexture(ts, floor_texture)
            self.add_cube(-1, x).setTexture(ts, floor_texture)
            self.add_cube(self.size[1], x).setTexture(ts, floor_texture)

    def add_cube(self, x, y, z = 0):
        cube = self.render.attachNewNode(Cube())
        ts = TextureStage('ts')
        ts.setMode(TextureStage.MModulate)
        cube.setTexture(ts, self.wall_texture)
        cube.setTwoSided(True)
        cube.setPos(x, y, 0)
        cube.setScale(0.5, 0.5, 0.5)
        self.objs.append(cube)
        return cube

    def add_lights(self, x, y):
        self.render.setShaderAuto() # Important! Enable the shader generator.

        light1 = Spotlight('light1')
        light1.setColor((0.8, 0.8, 0.8, 0.8))
        light1.setLens(PerspectiveLens())
        light1.setShadowCaster(True)
        node1 = self.render.attachNewNode(light1)
        node1.setPos(x, y, 300)
        node1.lookAt(x, y, 0)
        self.render.setLight(node1)
        self.lgts.append(node1)

        light2 = AmbientLight("light2")
        light2.setColor((0.2, 0.2, 0.2, 0.2))
        node2 = self.render.attachNewNode(light2)
        self.render.setLight(node2)
        self.lgts.append(node2)

        light3 = DirectionalLight("light3")
        light3.setDirection(LVector3(-1, -1, -1))
        light3.setColor((0.2, 0.2, 0.2, 1))
        light3.setSpecularColor((1, 1, 1, 1))
        light3.setShadowCaster(True)
        node3 = self.render.attachNewNode(light3)
        self.render.setLight(node3)
        self.lgts.append(node3)

    def display_help(self):
        title = OnscreenText(text="Magic Maze",
                             style=1, fg=(1, 1, 1, 1), pos=(0, 0.01), scale=.1,
                             parent=self.a2dBottomRight, align=TextNode.ARight)
        toggle_view = OnscreenText(text="0. global/role view",
                             style=1, fg=(1, 1, 1, 1), pos=(0, 0.10), scale=.07,
                             parent=self.a2dBottomRight, align=TextNode.ARight)
        generate = OnscreenText(text="1. generate maze",
                             style=1, fg=(1, 1, 1, 1), pos=(0, 0.15), scale=.07,
                             parent=self.a2dBottomRight, align=TextNode.ARight)
        auto_maze = OnscreenText(text="2. auto run maze",
                             style=1, fg=(1, 1, 1, 1), pos=(0, 0.20), scale=.07,
                             parent=self.a2dBottomRight, align=TextNode.ARight)
        sliderText = OnscreenText("Size", pos = (-0.35, -0.965), scale = .07, fg = (1, 1, 1, 1))
        self.slider = DirectSlider(pos = (0, 0, -0.95), scale = 0.25, value = .50)
        # self.slider.guiItem.getValue()


def main():
    app = MyApp()
    app.run()


if __name__ == '__main__':
    main()