打包命令
pyinstaller -D demo/ht_test.py --noconfirm
打包完后，把easytrader拷贝到对应目录下

# 安装venv环境
python -m venv venv

切换到 venv/Scripts, 执行activate.bat，然后执行 pip install ../../requirements.txt安装依赖