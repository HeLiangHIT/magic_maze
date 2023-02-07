#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2023-01-18 16:30:36
# @Author  : HeLiang (helianghit@foxmail.com)
# @Link    : https://github.com/HeLiangHIT
# @ref     : https://doc.qt.io/qtforpython/PySide6/QtWidgets/QGraphicsView.html#qgraphicsview

'''
pyqt 编写的贪吃蛇界面
'''
import os
import sys
import time
from functools import reduce
import copy
from PyQt5 import QtCore, QtGui, QtWidgets, Qt, QtTest
from PyQt5.QtWidgets import QApplication
from algorithm.map import Point, Map
from algorithm.search import bfs, dfs, a_star
from algorithm.generate import dfsg, primg, kruskalg


_script_dir = os.path.dirname(os.path.realpath(__file__))


class MazeMain(QtWidgets.QWidget):
    DEFAULT = (15, 20) # 默认迷宫尺寸
    MAX = (300, 400) # 最大支持的迷宫尺寸
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()
        self.gen_btn.clicked.connect(self.generate_maze)
        self.draw_btn.clicked.connect(self.draw_maze)
        self.run_btn.clicked.connect(self.run_maze)
        self.auto_btn.clicked.connect(self.auto_maze)
        self.load_btn.clicked.connect(self.load_maze)
        self.save_btn.clicked.connect(self.save_maze)
        # 自动修改终点位置
        self.maze_height.textChanged.connect(lambda x: self.end_x.setText("%s" % (int(x) - 1)))
        self.maze_width.textChanged.connect(lambda x: self.end_y.setText("%s" % (int(x) - 1)))

    def load_maze(self):
        path, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选择文件", './demo', "Map Files(*.map)")
        if not path:
            return
        with open(path, 'r') as f:
            self.maze_map, ok = Map().from_json(f.read())
            if not ok:
                QtWidgets.QMessageBox.information(self, "文件无效", "无法解析该文件", QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.Yes)
                return
        self.size, self.start, self.end = self.maze_map.size, self.maze_map.start[0], self.maze_map.end[0]
        [e.setText(str(v)) for e, v in zip((self.maze_height, self.maze_width, self.start_x, self.start_y, self.end_x, self.end_y), self.size + self.start + self.end)]
        self.maze.new_maze(self.maze_map)

    def save_maze(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', f'./demo/{self.size[0]}X{self.size[1]}.map')
        if not path:
            return
        with open(path,'w') as f:
            f.write(self.maze_map.to_json())

    def draw_maze(self):
        # 鼠标左键绘制通道/墙体
        if not self.is_drawing:
            self._start_draw()
        else:
            self._finish_draw()
        self.is_drawing = not self.is_drawing
    def _finish_draw(self):
        if self.draw_btn.text().count("完成") > 0:
            self.maze_map = self.maze.get_map()
        self.maze.new_maze(self.maze_map)
        [btn.setDisabled(False) for btn in (self.gen_btn, self.run_btn, self.auto_btn)]
        self.draw_btn.setText("绘制迷宫")
    def _start_draw(self):
        [btn.setDisabled(True) for btn in (self.gen_btn, self.run_btn, self.auto_btn)]
        self.draw_btn.setText("无效迷宫，取消绘制")
        def fresh_and_check(m):
            answers = a_star(m.data, [self.start,], [self.end,])
            self.draw_btn.setText(("无效迷宫，取消绘制", "有效迷宫，完成绘制")[len(answers) > 0])
        self.size, self.start, self.end = self._parser_input_text()
        m = Map(self.size, default = Point.Wall)
        m.data[self.start[0]][self.start[1]] = Point.Start
        m.data[self.end[0]][self.end[1]] = Point.End
        self.maze.new_maze(m, callback = fresh_and_check, mode = "draw") # 注册绘制的回调函数

    def run_maze(self):
        # 鼠标左键绘制路线，右键消除路线 - 走迷宫的时候重新生成或者自动走都不会影响绘制，可以不禁用其它按钮
        def fresh_and_check(m):
            # 检查终点附近是不是已经走到了
            udlr = [(self.end[0] - 1, self.end[1]), (self.end[0] + 1, self.end[1]), (self.end[0], self.end[1] - 1), (self.end[0], self.end[1] + 1),]
            visited_nb = reduce(lambda x, y: x + y, 
                                [0 <= q[0] < self.size[0] and 0 <= q[1] < self.size[1] and m.data[q[0]][q[1]] in (Point.Start, Point.Visited) for q in udlr])
            if visited_nb >= 1:
                ndata = [[Point.Chan if p in (Point.Visited, Point.Start, Point.End) else Point.Wall for p in row] for row in m.data] # 用于根据走的路径寻找答案
                answers = bfs(ndata, [self.start, ], [self.end, ])
                self.maze.new_maze(self.maze_map, answers[0]) # 重绘答案
                QtWidgets.QMessageBox.information(self, "恭喜通关", "恭喜通关", QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.Yes)
        self.maze.new_maze(self.maze_map, callback = fresh_and_check, mode = "run") # 注册绘制的回调函数

    def generate_maze(self):
        idx = self.gen_combo.currentIndex()
        generate = {0: primg, 1: dfsg}[idx]
        self.size, self.start, self.end = self._parser_input_text()
        self.maze_map = generate(self.size, [self.start, ], [self.end, ], callback = self._fresh_callback if self.visible_check.isChecked() else None)
        self.maze.new_maze(self.maze_map)

    def auto_maze(self):
        idx = self.auto_combo.currentIndex()
        search = {0: bfs, 1: dfs, 2: a_star}[idx]
        answers = search(self.maze_map.data, [self.start,], [self.end,], callback = self._fresh_callback if self.visible_check.isChecked() else None)
        answer = answers[0] if len(answers) > 0 else []
        self.maze.new_maze(self.maze_map, answer)

    def _fresh_callback(self, data, interval = 0.01):
        speed = self.speed_slider.value()
        interval = (1e-7, 1e-4, 1e-1)[(speed < 33) + (speed < 66)] # 三个档慢、中、快
        m = Map().from_data(data)
        self.maze.update_maze(m)
        # QApplication.processEvents() # 强制刷新界面 - 性能较差，改为在组件中 repaint
        # time.sleep(interval) # 会卡UI
        QtTest.QTest.qWait(interval * 1000) # 单位 msecs, 不卡UI

    def _parser_input_text(self):
        size = (int(self.maze_height.text()), int(self.maze_width.text()))
        start = (int(self.start_x.text()), int(self.start_y.text()))
        end = (int(self.end_x.text()), int(self.end_y.text()))
        return size, start, end

    def init_ui(self):
        self.resize(1024, 624)
        self.setWindowTitle("Maze")
        self.setWindowIcon(QtGui.QIcon(os.path.sep.join([_script_dir, "resources", "maze.png"])))
        h_layout_main = QtWidgets.QHBoxLayout(self)
        h_layout_main.setContentsMargins(2, 2, 2, 2)

        self.maze = MazeWidget()
        self.maze.setStyleSheet("margin:0px; padding:0px; background:rgba(0,0,0,0); border:none;")
        h_layout_main.addWidget(self.maze)

        v_layout_right = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setFamily("Lucida Calligraphy")
        font.setPointSize(28)
        title.setFont(font)
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setText("Maze")
        v_layout_right.addWidget(title)

        gb = QtWidgets.QGroupBox("通用输入", self)
        v_layout_input = QtWidgets.QVBoxLayout()
        h_layout_size = QtWidgets.QHBoxLayout()
        size_text = QtWidgets.QLabel(gb)
        size_text.setText("尺寸: ")
        h_layout_size.addWidget(size_text)
        self.maze_height = QtWidgets.QLineEdit(gb)
        self.maze_height.setText("%s" % self.DEFAULT[0])
        self.maze_height.setValidator(QtGui.QIntValidator(3, self.MAX[0]))
        h_layout_size.addWidget(self.maze_height)
        size_spliter = QtWidgets.QLabel(gb)
        size_spliter.setText("X")
        h_layout_size.addWidget(size_spliter)
        self.maze_width = QtWidgets.QLineEdit(gb)
        self.maze_width.setText("%s" % self.DEFAULT[1])
        self.maze_width.setValidator(QtGui.QIntValidator(3, self.MAX[1]))
        h_layout_size.addWidget(self.maze_width)
        v_layout_input.addLayout(h_layout_size)
        
        h_layout_start = QtWidgets.QHBoxLayout()
        start_text = QtWidgets.QLabel(gb)
        start_text.setText("起点: ")
        h_layout_start.addWidget(start_text)
        self.start_x = QtWidgets.QLineEdit(gb)
        self.start_x.setText("0")
        self.start_x.setValidator(QtGui.QIntValidator(0, self.MAX[0] - 1))
        h_layout_start.addWidget(self.start_x)
        start_spliter = QtWidgets.QLabel(gb)
        start_spliter.setText(",")
        h_layout_start.addWidget(start_spliter)
        self.start_y = QtWidgets.QLineEdit(gb)
        self.start_y.setText("0")
        self.start_y.setValidator(QtGui.QIntValidator(0, self.MAX[1] - 1))
        h_layout_start.addWidget(self.start_y)
        v_layout_input.addLayout(h_layout_start)

        h_layout_end = QtWidgets.QHBoxLayout()
        end_text = QtWidgets.QLabel(gb)
        end_text.setText("终点: ")
        h_layout_end.addWidget(end_text)
        self.end_x = QtWidgets.QLineEdit(gb)
        self.end_x.setText("%s" % (self.DEFAULT[0] - 1))
        self.end_x.setValidator(QtGui.QIntValidator(0, self.MAX[0] - 1))
        h_layout_end.addWidget(self.end_x)
        end_spliter = QtWidgets.QLabel(gb)
        end_spliter.setText(",")
        h_layout_end.addWidget(end_spliter)
        self.end_y = QtWidgets.QLineEdit(gb)
        self.end_y.setText("%s" % (self.DEFAULT[1] - 1))
        self.end_y.setValidator(QtGui.QIntValidator(0, self.MAX[1] - 1))
        h_layout_end.addWidget(self.end_y)
        v_layout_input.addLayout(h_layout_end)

        gb.setLayout(v_layout_input)
        v_layout_right.addWidget(gb)

        gb = QtWidgets.QGroupBox("自动操作", self)
        v_layout_auto = QtWidgets.QVBoxLayout()

        h_layout_visible = QtWidgets.QHBoxLayout()
        self.visible_check = QtWidgets.QCheckBox("显示/速度:", self)
        self.visible_check.setChecked(False) # isChecked
        h_layout_visible.addWidget(self.visible_check)
        self.speed_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.speed_slider.setTickInterval(33)
        self.speed_slider.setValue(50)
        self.speed_slider.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        h_layout_visible.addWidget(self.speed_slider) # value()
        v_layout_auto.addLayout(h_layout_visible)

        h_layout_gen = QtWidgets.QHBoxLayout()
        self.gen_combo = QtWidgets.QComboBox(self)
        self.gen_combo.addItem("Prim算法")
        self.gen_combo.addItem("深度优先")
        # self.gen_combo.addItem("Kruskal算法") # TODO: 待开发
        h_layout_gen.addWidget(self.gen_combo)
        self.gen_btn = QtWidgets.QPushButton(self)
        self.gen_btn.setText("生成迷宫")
        h_layout_gen.addWidget(self.gen_btn)
        v_layout_auto.addLayout(h_layout_gen)

        h_layout_auto = QtWidgets.QHBoxLayout()
        self.auto_combo = QtWidgets.QComboBox(self)
        self.auto_combo.addItem("BFS")
        self.auto_combo.addItem("DFS")
        self.auto_combo.addItem("A*")
        h_layout_auto.addWidget(self.auto_combo)
        self.auto_btn = QtWidgets.QPushButton(self)
        self.auto_btn.setText("走迷宫")
        h_layout_auto.addWidget(self.auto_btn)
        v_layout_auto.addLayout(h_layout_auto)

        gb.setLayout(v_layout_auto)
        v_layout_right.addWidget(gb)

        gb = QtWidgets.QGroupBox("手动操作", self)
        v_layout_handle = QtWidgets.QVBoxLayout()
        self.draw_btn = QtWidgets.QPushButton(self)
        self.draw_btn.setText("绘制迷宫")
        self.is_drawing = False
        v_layout_handle.addWidget(self.draw_btn)
        self.run_btn = QtWidgets.QPushButton(self)
        self.run_btn.setText("走迷宫")
        v_layout_handle.addWidget(self.run_btn)
        notice_lbl = QtWidgets.QLabel(self)
        notice_lbl.setStyleSheet("QLabel{font-size:6pt;font-family:宋体;font-style:italic;text-align:center;}")
        notice_lbl.setText("左键绘制/右键清除/触摸翻转")
        notice_lbl.setAlignment(QtCore.Qt.AlignCenter)
        v_layout_handle.addWidget(notice_lbl)

        gb.setLayout(v_layout_handle)
        v_layout_right.addWidget(gb)

        gb = QtWidgets.QGroupBox("加载/保存", self)
        h_layout_handle = QtWidgets.QHBoxLayout()
        self.load_btn = QtWidgets.QPushButton(self)
        self.load_btn.setText("加载")
        h_layout_handle.addWidget(self.load_btn)
        self.save_btn = QtWidgets.QPushButton(self)
        self.save_btn.setText("保存")
        h_layout_handle.addWidget(self.save_btn)

        gb.setLayout(h_layout_handle)
        v_layout_right.addWidget(gb)

        right_widget = QtWidgets.QWidget() # 为了控制右侧宽度
        right_widget.setFixedWidth(224)
        right_widget.setLayout(v_layout_right)
        h_layout_main.addWidget(right_widget)

        # self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        # self.setFixedSize(self.width(), self.height())
        self.generate_maze()

class MazeWidget(QtWidgets.QWidget):
    ColorMap = {
        Point.Wall: QtCore.Qt.black,
        Point.Start: QtCore.Qt.blue,
        Point.End: QtCore.Qt.blue,
        Point.Visited: QtCore.Qt.cyan,
        Point.NxtVisit: QtCore.Qt.gray,
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_AcceptTouchEvents, True) # 允许触摸响应
        self.m = None

    def new_maze(self, maze_map, answer = None, callback = None, mode = "display"):
        # 新的迷宫数据
        self.m = copy.deepcopy(maze_map)
        self.answer = answer if answer is not None else []
        self.col_num = maze_map.size[1] # 列 -> 二维
        self.row_num = maze_map.size[0]
        self.callback = callback
        self.diff = None
        self.pix = None
        self.mode = mode
        self.repaint() # 强制刷新迷宫

    def update_maze(self, maze_map):
        # 增量刷新迷宫显示区域
        if self.m is None or self.m.size != maze_map.size:
            self.new_maze(maze_map) # 首次设置
        else:
            self.diff = self.m.diff(maze_map)
            self.m = copy.deepcopy(maze_map)
            self.pix = self.grab(QtCore.QRect(0, 0, self.width(), self.height())) # 避免仅显示绘制部分，作为二级缓存显示
            self.repaint()

    def get_map(self):
        return copy.deepcopy(self.m)

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QtGui.QPainter(self)
        self.col_len = self.width() / self.col_num
        self.row_len = self.height() / self.row_num
        if self.diff and self.pix:
            painter.drawPixmap(0, 0, self.width(), self.height(), self.pix)
            self._draw_diff(painter)
        else:
            self._draw_all(painter)
            self._draw_answer(painter)

    def _draw_all(self, painter):
        # 绘制迷宫
        for m in range(self.col_num):
            for n in range(self.row_num):
                color = self.ColorMap[self.m.data[n][m]] if self.m.data[n][m] in self.ColorMap.keys() else QtCore.Qt.white
                painter.setPen(color)
                painter.setBrush(color)
                painter.drawRect(m * self.col_len, n * self.row_len, self.col_len, self.row_len)
                if self.m.data[n][m] == Point.Start:
                    painter.drawImage(QtCore.QRect(m * self.col_len, n * self.row_len, self.col_len, self.row_len), 
                        QtGui.QImage(os.path.sep.join([_script_dir, "resources", "run.png"])))
                if self.m.data[n][m] == Point.End:
                    painter.drawImage(QtCore.QRect(m * self.col_len, n * self.row_len, self.col_len, self.row_len), 
                        QtGui.QImage(os.path.sep.join([_script_dir, "resources", "flag.png"])))

    def _draw_diff(self, painter):
        # 绘制增量
        for n, m, v in self.diff:
            color = self.ColorMap[v] if v in self.ColorMap.keys() else QtCore.Qt.white
            painter.setPen(color)
            painter.setBrush(color)
            painter.drawRect(m * self.col_len, n * self.row_len, self.col_len, self.row_len)

    def _draw_answer(self, painter):
        # 绘制答案
        for n, m in self.answer[1:-1]: # 起止点有专门的标记，不用重复绘制
            painter.setPen(QtCore.Qt.yellow)
            painter.setBrush(QtCore.Qt.red)
            painter.drawEllipse(m * self.col_len + self.col_len / 4, n * self.row_len + self.row_len / 4, 
                                self.col_len / 2, self.row_len / 2)

    def event(self, e):
        if e.type() not in (QtGui.QTouchEvent.TouchBegin, QtGui.QTouchEvent.TouchUpdate, QtGui.QTouchEvent.TouchEnd):
            return super().event(e)
        if self.mode == "run":
            self._flip_cell_for_run_maze(e.touchPoints()[0].pos(), QtCore.Qt.LeftButton)
        if self.mode == "draw":
            self._flip_cell_for_draw_maze(e.touchPoints()[0].pos(), QtCore.Qt.LeftButton)
        return True

    def mousePressEvent(self, e):
        self.mouseMoveEvent(e)

    def mouseMoveEvent(self, e):
        if self.mode == "run":
            self._flip_cell_for_run_maze(e.pos(), e.buttons())
        if self.mode == "draw":
            self._flip_cell_for_draw_maze(e.pos(), e.buttons())

    def _flip_cell_for_draw_maze(self, pos, btn):
        # 获取坐标所在迷宫位置并标记已访问，注意此处QT的坐标和矩阵是反的
        # 鼠标移动时翻转墙体和通道 - 支持触屏翻转
        row = int(pos.y() / self.row_len)
        col = int(pos.x() / self.col_len)
        # 确保鼠标没有移出边界
        if not (0 <= row < self.row_num and 0 <= col < self.col_num):
            return
        if self.m.data[row][col] == Point.Wall and btn == QtCore.Qt.LeftButton:
            self.m.data[row][col] = Point.Chan
        elif self.m.data[row][col] == Point.Chan and btn == QtCore.Qt.RightButton:
            self.m.data[row][col] = Point.Wall
        self.repaint() # 强制刷新迷宫
        if self.callback:
            self.callback(self.m)
        
    def _flip_cell_for_run_maze(self, pos, btn):
        # 获取坐标所在迷宫位置并标记已访问，注意此处QT的坐标和矩阵是反的
        # 鼠标移动时左键走路线、右键清除路线 - 触屏走迷宫时可以不需要清除路线
        row = int(pos.y() / self.row_len)
        col = int(pos.x() / self.col_len)
        # 确保鼠标没有移出边界
        if not (0 <= row < self.row_num and 0 <= col < self.col_num):
            return
        # 确保附近有访问过或者在起点边上才能走通 - 无法支持倒着走
        udlr = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1),]
        visited_nb = reduce(lambda x, y: x + y, 
                              [0 <= q[0] < self.row_num and 0 <= q[1] < self.col_num and self.m.data[q[0]][q[1]] in (Point.Start, Point.Visited) for q in udlr])
        if visited_nb != 1:
            return
        if self.m.data[row][col] == Point.Chan and btn == QtCore.Qt.LeftButton:
            self.m.data[row][col] = Point.Visited
        elif self.m.data[row][col] == Point.Visited and btn == QtCore.Qt.RightButton:
            self.m.data[row][col] = Point.Chan
        self.repaint() # 强制刷新迷宫
        if self.callback:
            self.callback(self.m)


def main():
    app = QApplication(sys.argv)
    gui = MazeMain()
    gui.show()
    return app.exec_()


if __name__ == '__main__':
    main()

