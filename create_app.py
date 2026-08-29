# -*- coding: utf-8 -*-
content = '''# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
import subprocess
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

API_KEY = "4Xl4a3FwEyaB1N3XHauyU3BOvFegzLKgWKBdAs0TqLU"
API_BASE = "https://api.jquants.com/v2"
VENV_PYTHON = r"C:\\\\stock_system\\\\venv\\\\Scripts\\\\python.exe"
DATA_DIR = r"C:\\\\stock_system"

st.set_page_config(page_title="Stock Analysis", layout="wide", page_icon="📈")

st.title("📈 株式分析システム")
st.write("起動テスト成功！")
'''

with open(r"C:\stock_system\app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("app.py を作成しました")