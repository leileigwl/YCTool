#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
远成国际报价系统
主应用入口
"""

from database import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("义乌耀灿太阳能报价系统启动中...")
    print("访问地址: http://localhost:5002")
    print("=" * 50)
    app.run(host='0.0.0.0', debug=False, port=5002)