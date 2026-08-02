@echo off
chcp 65001 >nul
:: 自动切换到脚本所在的目录
cd /d "%~dp0"
:: 激活Python虚拟环境
call .\venv\Scripts\activate.bat
:: 启动Streamlit压缩工具
streamlit run app.py
:: 程序结束后保留窗口，方便查看报错信息
pause