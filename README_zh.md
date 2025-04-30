# 模块化机器人手臂控制系统

一个用于控制机器人手臂的模块化系统，集成了计算机视觉功能。该项目提供了一个框架，通过摄像头检测物体并引导机器人手臂进行抓取、放置和操作。

## 功能特点

- **物体检测**：基于颜色的物体检测和跟踪
- **机器人控制**：控制亚博 MyCobot 280 机器人手臂
- **管道架构**：模块化管道系统，具有基于优先级的信号处理
- **FastAPI 集成**：用于控制管道和发送信号的现代 Web API
- **进程管理**：可靠管道执行的多进程架构
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
2. 默认端口设置为 `/dev/ttyUSB0`。如果您的机器人连接到不同的端口，您需要在配置中指定它。

## 使用方法

### 启动服务器

使用特定管道运行服务器：

```bash
python -m backend.main --pipeline yahboom_pick_and_place
```

或通过环境变量设置初始管道：

```bash
PIPELINE=yahboom_pick_and_place DEBUG=true python -m backend.main
```

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
- `examples/`：客户端演示代码
- `docs/`：文档文件

## 待办事项

- **Redis 集成**：用基于 Redis 的图像流替换阻塞的 imagezmq
- **Web 前端**：开发用于可视化处理器结果和控制管道的前端界面
- **实时可视化**：将中间处理结果流式传输到 UI
