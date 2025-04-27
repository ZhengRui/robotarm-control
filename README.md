# 模块化机器人手臂控制系统

机器人手臂控制项目，提供视频流处理和分析功能。

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/Modu-RobotArm-Control.git
cd Modu-RobotArm-Control

# 安装依赖
python -m venv venv
venv\Scripts\activate  # Windows
# 或
source venv/bin/activate  # Linux/Mac

# 安装项目及开发依赖
pip install -e .
pip install -e ".[dev]"
```

### 开发设置

```bash
# 设置预提交钩子
pre-commit install

# 代码格式化
ruff format .
```

### 启动服务

```bash
# 服务器端
python server.py --handler your_handler_name

# 客户端（摄像头）
python examples/streaming.py --source webcam:0 --server 127.0.0.1

# 客户端（视频文件）
python examples/streaming.py --source path/to/video.mp4 --server 127.0.0.1
```

## 项目结构

```
├── examples/          # 示例代码
├── utils/             # 工具函数
├── server.py          # 服务器端
└── pyproject.toml     # 项目配置
```

## 自定义处理器

创建处理器需实现两个方法：
- `process(frame)`：处理输入帧
- `visualize(frame, result)`：可视化结果
