# 模块化机器人手臂控制系统

一个用于控制机器人手臂的模块化系统，集成了计算机视觉功能。该项目提供了一个框架，通过摄像头检测物体并引导机器人手臂进行抓取、放置和操作。

## 功能特点

- **物体检测**：基于颜色的物体检测和跟踪
- **机器人控制**：控制亚博 MyCobot 280 机器人手臂
- **管道架构**：模块化管道系统，具有基于优先级的信号处理
- **FastAPI 集成**：用于控制管道和发送信号的现代 Web API
- **进程管理**：可靠管道执行的多进程架构
- **Redis 集成**：非阻塞图像流传输与内存管理
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
   cd backend
   uv venv
   source .venv/bin/activate  # 在 Windows 上，使用 .venv\Scripts\activate
   ```

3. 使用 uv 安装依赖：
   ```bash
   uv sync
   ```

### 机器人手臂设置

1. 通过 USB 将亚博 MyCobot 280 连接到您的计算机
2. 默认端口设置为 `/dev/ttyUSB0`。如果您的机器人连接到不同的端口，您需要在配置中指定它。

## 使用方法

### 配置

系统使用位于 `backend/config/` 目录中的 YAML 配置文件：

- `dev.yaml`：开发环境配置
- `prod.yaml`：生产环境配置

您可以复制示例文件来创建自己的配置：

```bash
cp backend/config/dev.example.yaml backend/config/dev.yaml
cp backend/config/prod.example.yaml backend/config/prod.yaml
```

编辑这些文件以调整设置，如：
- 机器人手臂端口和连接参数
- 图像处理参数
- 管道默认行为
- Redis 连接设置

### 启动服务器

以调试模式启动服务器：

```bash
DEBUG=true python train.py
```

如需更多控制，可以指定管道：

```bash
PIPELINE=yahboom_pick_and_place DEBUG=true python train.py
```

### 运行流媒体客户端

向系统流式传输视频：

```bash
python -m examples.streaming --source /path/to/video.mp4 --keep_size --lossless --enable_freeze --visualization --max-frames 100 --time-window 2
```

选项：
- `--source`：视频文件、网络摄像头（webcam:0）或图像目录
- `--keep_size`：保持原始图像尺寸
- `--lossless`：使用无损编码传输帧
- `--enable_freeze`：允许使用空格键暂停流
- `--visualization`：显示带有可视化效果的视频流
- `--max-frames`: 设置 Redis 内存管理的最大保存帧数
- `--time-window`：设置 Redis 内存管理的时间窗口（以秒为单位）

### API 端点

系统提供以下 API 端点：

- `GET /pipelines`：列出所有可用和正在运行的管道
- `POST /pipelines/start`：启动特定管道
- `POST /pipelines/stop`：停止正在运行的管道
- `POST /signal`：向正在运行的管道发送信号
- `GET /status`：获取管道的详细状态信息

### 示例请求

启动管道：
```bash
curl -X POST "http://localhost:8000/pipelines/start" -H "Content-Type: application/json" -d '{"pipeline_name": "yahboom_pick_and_place", "debug": true}'
```

发送信号：
```bash
curl -X POST "http://localhost:8000/signal?pipeline_name=yahboom_pick_and_place" -H "Content-Type: application/json" -d '{"signal": "pick_red", "priority": "HIGH"}'
```

## 项目结构

- `backend/`：主服务器实现
  - `app/`：FastAPI 应用程序和端点
  - `lib/`：核心功能
    - `pipelines/`：基于进程架构的管道实现
    - `handlers/`：用于视觉和机器人控制的专门处理器
    - `utils/`：辅助函数和工具
  - `config/`：不同环境的配置文件
- `examples/`：客户端演示代码
- `docs/`：文档文件

## 后续计划

- **Web 前端**：开发用于可视化处理器结果和控制管道的前端界面
- **实时可视化**：将中间处理结果流式传输到 UI
- **额外机器人型号**：支持不同的机器人手臂型号和配置
