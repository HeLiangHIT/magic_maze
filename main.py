#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2023-01-17 21:55:23
# @Author  : HeLiang (helianghit@foxmail.com)
# @Link    : https://github.com/HeLiangHIT


def main(dimension:str = "2d"):
    ''' magic maze game in 2d and 3d dimension
    Args:
        dimension: Optional: "2d"/"3d"
    Return:
        None
    '''
    if dimension == "3d":
        from ui.panda3d.main import main
        main()
    else:
        from ui.pyqt.main import main
        main()


def cmd_main():
    import fire
    fire.Fire(main)

if __name__ == '__main__':
    import fire
    fire.Fire(main)
