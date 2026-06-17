"""Marvis Calendar — 个人桌面日历入口"""

import sys
import os

# 确保 src 在 path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.app import main

if __name__ == "__main__":
    main()
