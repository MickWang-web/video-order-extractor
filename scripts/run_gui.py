#!/usr/bin/env python3
"""
启动GUI应用的脚本
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui_app import main

if __name__ == "__main__":
    main()
