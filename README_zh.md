# 模块化机器人手臂控制系统

一个用于控制机器人手臂的模块化系统，集成了计算机视觉功能。该项目提供了一个框架，通过摄像头检测物体并引导机器人手臂进行抓取、放置和操作。

## 功能特点

- **物体检测**：基于颜色的物体检测和跟踪
- **机器人控制**：控制亚博 MyCobot 280 机器人手臂
- **客户端-服务器架构**：图像处理服务器与客户端摄像头分离
- **模块化设计**：可替换不同的处理器用于检测、校准和控制
- **可配置性**：适应不同的机器人设置、检测参数和任务

## 安装

### 前提条件

- Python 3.8 或更新版本
- 通过 USB 连接到机器人手臂（用于控制功能）
- 摄像头（USB 网络摄像头、IP 摄像头或视频文件）

### 设置

1. 克隆仓库：
   ```bash
   git clone [repository-url]
   cd modulus-robotarm-control
   ```

2. 使用 uv 创建并激活虚拟环境：
   ```bash
   uv venv
   source .venv/bin/activate  # 在 Windows 上，使用 .venv\Scripts\activate
   ```

3. 使用 uv 安装依赖：
   ```bash
   uv sync
   ```

### 机器人手臂设置

1. 通过 USB 将亚博 MyCobot 280 连接到您的计算机
2. 默认端口设置为 `/dev/ttyUSB0`。如果您的机器人连接到不同的端口，您需要在运行处理器时指定它。

## 使用方法

### 启动服务器

使用特定处理器运行服务器：

```bash
python server.py --handler detect
```

可用的处理器：
- `detect`：仅用于物体检测
- `calibrate`：用于校准摄像头到机器人坐标系统
- `armcontrol`：用于带有物体检测的机器人手臂控制

使用 `--debug` 标志启用可视化：

```bash
python server.py --handler detect --debug
```

### 运行客户端

客户端将图像流传输到服务器进行处理：

```bash
python -m examples/streaming.py --source webcam:0 --server 127.0.0.1
```

`--source` 的选项：
- `webcam:0`、`webcam:1` 等：用于网络摄像头设备
- 视频文件路径：用于从录制的视频流传输
- 图像或图像目录的路径：用于处理静态图像

其他选项：
- `--max_size`：图像较长边的最大尺寸（默认：800）
- `--keep_size`：保持原始图像尺寸
- `--jpg_quality`：JPEG 压缩质量（1-100）
- `--lossless`：发送不压缩的原始帧
- `--autoplay`：自动浏览图像源
- `--enable_freeze`：使用空格键暂停
- `--write_to`：保存处理图像的目录

## 项目结构

- `server.py`：主服务器实现
- `handlers/`：针对不同任务的专门模块
  - `detect.py`：物体检测处理器
  - `armcontrol.py`：机器人手臂控制处理器
  - `calibrate.py`：校准处理器
- `examples/`：客户端演示代码
- `utils/`：辅助工具
- `docs/`：文档文件
  - `status.md`：详细状态报告
  - `pymycobot_api_docs.md`：机器人 API 文档

## 自定义处理器

创建处理器需实现两个方法：
- `process(frame)`：处理输入帧
- `visualize(frame, result)`：可视化结果
