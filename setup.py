#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2023-01-31 16:02:56
# @Author  : HeLiang (helianghit@foxmail.com)
# @Link    : https://github.com/HeLiangHIT
# @Ref     : https://zhuanlan.zhihu.com/p/276461821?utm_source=wechat_session
#            https://www.zhihu.com/question/20609631
import os
from setuptools import setup


def sub_path(rpath):
    script_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.sep.join([script_dir, rpath])


def read_file(path):
    with open(path, 'r') as f:
        return f.read()
    return ''


def get_latest_tag():
    from git.repo import Repo # 需在发布机上 pip install gitpython
    tags = Repo().tags
    if len(tags) > 0:
        return tags[-1].name
    else:
        return 'v0.0.0' # 初始版本号


def list_packages():
    import pkgutil
    return [name for _, name, ispkg in pkgutil.walk_packages([sub_path('.'),] ) if ispkg]


def list_modules():
    import pkgutil
    return [name for _, name, ispkg in pkgutil.walk_packages([sub_path('.'),] ) if not ispkg]


def find_files(directory, strip = os.path.abspath(os.path.dirname(__file__))):
  result = []
  for root, dirs, files in os.walk(directory):
    for filename in files:
      filename = os.path.join(root, filename)
      result.append(os.path.relpath(filename, strip))
  return result


setup(
    name = 'magic_maze',
    version = get_latest_tag(),
    url = 'https://github.com/HeLiangHIT/magic_maze',
    license = 'Mulan PSL v2',
    author = 'He Liang',
    author_email = 'heianghit@foxmail.com',
    keywords = 'maze pyqt',

    description = 'maze game developed by python',
    long_description = 'maze game developed by python', # read_file(sub_path('README.md'))

    packages = list_packages(),
    py_modules = list_modules(),
    install_requires = read_file(sub_path('requirement.txt')).split('\n'),
    entry_points = {'console_scripts': [
        'maze = main:main', # cmd entry points
    ]},
    data_files = [('', ['README.md', 'LICENSE']),
                  ('script', find_files(sub_path("script"))),
                  ('demo', find_files(sub_path("demo"))),
                  ('doc', find_files(sub_path("doc"))),
                  ('ui/resources', find_files(sub_path("ui/resources"))),],

    zip_safe = False, # avoid error when uninstall on windows

    classifiers = [
        'Programming Language :: Python :: 3',
        'Development Status :: 5 - Production/Stable',
        'Natural Language :: Chinese (Simplified)',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop', 
        'Operating System :: OS Independent',
        'Topic :: Games/Entertainment',
        'License :: OSI Approved :: Mulan Permissive Software License v2 (MulanPSL-2.0)',
    ],
)