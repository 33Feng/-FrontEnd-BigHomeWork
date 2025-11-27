## 可能用到的指令：

## 把项目 clone 到本地后，进入 backend，在终端运行：
# pip install requests python-dotenv
# pip install markdown

# 运行后端：
# python3 main.py 或 python main.py

## 进入 frontend,在终端运行：
# npm install

# 运行前端：
# npm run serve

## 注意：关于大模型和图谱的调用问题：
## 如果图谱显示失败，则说明 python 文件没有调用成功，检查文件目录是否正确以及是否安装 python ；
## 如果图谱显示正常，但是大模型没有正确显示，查看报错，如果显示超时“timeout600000”则是由于大模型思考时间过长导致，重新询问即可；
## 如果图谱显示正常，但是大模型没有正常显示且报错 403，则属于网络错误，请检查网络
## 如果显示 402 报错，则是 DeepSeek 额度不足导致，充值即可解决
