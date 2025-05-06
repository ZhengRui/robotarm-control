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
- **现代化 Web 仪表盘**：用于监控和控制系统的 Next.js 前端界面

## 项目结构

- `backend/`：服务器端实现
  - `app/`：FastAPI 应用程序和端点
  - `lib/`：核心功能
    - `pipelines/`：基于进程架构的管道实现
    - `handlers/`：用于视觉和机器人控制的专门处理器
    - `utils/`：辅助函数和工具
  - `config/`：不同环境的配置文件
- `frontend/`：Next.js 仪表盘
  - 用于监控和控制管道的现代用户界面
  - 用于实时更新的 WebSocket 集成
- `examples/`：客户端演示代码
- `.hooks/`：项目全局 git hooks
- `docs/`：文档文件

## 后端设置

### 前提条件

- Python 3.8 或更新版本
- 通过 USB 连接到机器人手臂（用于控制功能）
- 摄像头（USB 网络摄像头、IP 摄像头或视频文件）

### 安装

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
对于中国用户或遇到网络问题的用户：
   ```bash
   uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple
   ```

### 机器人手臂设置

1. 通过 USB 将亚博 MyCobot 280 连接到您的计算机
2. 默认端口设置为 `/dev/ttyUSB0`。如果您的机器人连接到不同的端口，您需要在配置中指定它。

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

### 启动后端服务器

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

## 前端设置

### 技术栈

- **Next.js**：带有服务器端渲染的 React 框架
- **TypeScript**：类型安全的 JavaScript
- **Tailwind CSS**：实用优先的 CSS 框架
- **Shadcn/UI**：高质量、可访问的 UI 组件

### 架构

- **后端通信**：
  - 用于基本操作的 REST API（列出管道、启动/停止）
  - 用于实时更新和流传输的 WebSocket 桥接
  - 用于后端管道通信的 Redis

- **UI 布局**：
  - 左侧边栏：用于管道设置的可折叠配置面板
  - 主区域：流帧和管道输出的可视化

### 安装

```bash
# 导航到前端目录
cd frontend

# 安装依赖
bun install

# 运行开发服务器
bun run dev
```

### 构建

```bash
# 为生产环境构建
bun run build

# 启动生产服务器
bun run start
```

### 功能

- 管道管理（列出、启动、停止）
- 配置编辑
- 信号控制
- 实时帧可视化
- 状态监控

## Git Hooks 设置

本项目使用 git hooks 确保代码质量和一致的提交消息。

### 设置钩子

1. 首先，在前端目录中准备 Husky 钩子：
   ```bash
   cd frontend
   bun run prepare:husky
   cd ..
   ```

2. 将钩子路径重置为使用项目的自定义钩子：
   ```bash
   git config core.hooksPath .hooks
   ```

这个两步过程确保了前端和后端钩子都正确安装。第一个命令在前端目录中设置 Husky，但它也会将 git 钩子路径更改为 `frontend/.husky`。第二个命令将钩子路径重置为项目根目录的 `.hooks` 目录，其中包含整个项目的钩子。

### 钩子功能

- **pre-commit**：为前端和后端代码运行代码检查和格式化
- **commit-msg**：根据约定式提交格式验证提交消息

## 后续计划

- **其他机器人型号**：支持不同的机器人手臂型号和配置
- **增强 UI 功能**：扩展仪表盘功能，提供更好的可视化和控制
- **实时分析**：添加指标和性能监控
