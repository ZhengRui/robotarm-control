# Modulus 机械臂控制系统

一个用于控制机械臂的模块化系统，集成了计算机视觉功能。该项目提供了一个框架，用于使用摄像头检测物体并引导机械臂拾取、放置和操作它们。

## 功能特点

- **物体检测**：基于颜色的物体检测和跟踪
- **机器人控制**：控制 Yahboom MyCobot 280 机械臂
- **管道架构**：模块化管道系统，具有基于优先级的信号处理功能
- **FastAPI 集成**：用于控制管道和发送信号的现代 Web API
- **进程管理**：基于多进程架构的可靠管道执行
- **Redis 集成**：具有内存管理的非阻塞图像流传输
- **WebSocket 集成**：向前端提供实时更新和数据流
- **可配置性**：基于工厂模式的处理器系统，具有分层配置
- **现代 Web 仪表盘**：用于监控和控制系统的 Next.js 前端

## 项目结构

- `backend/`：服务器端实现
  - `app/`：FastAPI 应用程序和端点
    - `api/`：REST 和 WebSocket 端点
    - `utils/`：辅助工具，包括 WebSocket 管理器
    - `config.py`：中央配置加载器
  - `lib/`：核心功能
    - `pipelines/`：基于进程的管道实现
      - `base.py`：管道的抽象基类
      - `factory.py`：管道注册和创建
      - `manager.py`：多进程管道管理
      - `process.py`：管道的进程封装
      - `yahboom/`：针对特定管道的实现和处理器
    - `handlers/`：处理器框架
      - `base.py`：处理器接口定义
      - `factory.py`：处理器注册和创建
      - `data_loader.py`：数据加载处理器 (Redis, ImageZMQ)
    - `utils/`：辅助函数和工具
  - `config/`：环境特定配置文件
- `frontend/`：Next.js 仪表盘
  - `src/`：源代码
    - `app/`：Next.js 应用路由器组件
    - `components/`：可重用 UI 组件
    - `lib/`：工具函数和 API 客户端
    - `hooks/`：自定义 React 钩子，用于数据和 WebSocket
- `examples/`：客户端演示代码
- `.hooks/`：项目范围的 Git 钩子
- `docs/`：文档文件

## 后端设置

### 前提条件

- Python 3.8 或更新版本
- 机械臂的 USB 连接（控制功能）
- 摄像头（USB 网络摄像头、IP 摄像头或视频文件）
- Redis 服务器（用于数据流传输和管道通信）

### 安装

1. 克隆存储库：
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

3. 使用 uv 安装依赖项：
   ```bash
   uv sync
   ```

   对于中国用户或网络问题：
   ```bash
   uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple
   ```

### 机械臂设置

1. 通过 USB 将 Yahboom MyCobot 280 连接到您的计算机
2. 默认端口设置为 `/dev/ttyUSB0`。如果您的机器人连接到不同的端口，您需要在配置中指定它。

### 配置系统

系统采用多层配置方法：

1. **管道默认配置**：
   - 位于 `lib/pipelines/[pipeline_type]/config.yaml`
   - 定义每种管道类型的默认设置
   - 包含处理器初始化和处理参数
   - 包含各个处理器的调试设置

2. **环境覆盖**：
   - 位于 `config/[env].yaml`（例如，`dev.yaml`，`prod.yaml`）
   - 包含环境特定的覆盖
   - 通过 `ENV` 环境变量选择
   - 列出环境中所有可用的管道

您可以复制示例文件来创建自己的配置：

```bash
cp backend/config/dev.example.yaml backend/config/dev.yaml
cp backend/config/prod.example.yaml backend/config/prod.yaml
```

编辑这些文件以调整设置，如：
- 机械臂端口和连接参数
- 图像处理参数
- 管道默认行为
- Redis 连接设置
- 特定处理器的调试设置

### 启动后端服务器

启动服务器：

```bash
python main.py
```

您可以指定环境和初始管道：

```bash
ENV=dev PIPELINE=yahboom_pick_and_place python main.py
```

### 运行流媒体客户端

要将视频流传输到系统：

```bash
python -m examples.streaming --source webcam:0 --keep_size --lossless --enable_freeze --visualization --max-frames 100 --time-window 0.1
```

选项：
- `--source`：视频文件、网络摄像头（webcam:0）或图像目录
- `--keep_size`：保持原始图像尺寸
- `--lossless`：使用无损编码帧
- `--enable_freeze`：允许使用空格键暂停流
- `--visualization`：显示带有可视化的视频流
- `--max-frames`：设置 Redis 内存管理的最大帧数
- `--time-window`：设置 Redis 内存管理的时间窗口（秒）

### API 端点

系统公开以下 API 端点：

- `GET /pipelines`：列出配置文件中定义的所有可用管道（运行中和非运行中）
- `GET /pipeline`：获取特定管道的详细信息
- `POST /pipeline/start`：启动特定管道
- `POST /pipeline/stop`：停止运行中的管道
- `POST /pipeline/signal`：向运行中的管道发送信号

### WebSocket 端点

用于实时更新和数据流传输：

- `ws/pipeline`：流式传输实时管道状态更新和事件
- `ws/queue`：流式传输实时帧数据和处理结果

#### WebSocket 连接参数

- 管道 WebSocket：`ws://host:port/ws/pipeline?pipeline_name=<pipeline_name>`
- 队列 WebSocket：`ws://host:port/ws/queue?pipeline_name=<pipeline_name>&queue_name=<queue_name>`

### 示例请求

启动管道：
```bash
curl -X POST "http://localhost:8000/pipeline/start?pipeline_name=yahboom_pick_and_place" -H "Content-Type: application/json"
```

发送信号：
```bash
curl -X POST "http://localhost:8000/pipeline/signal?pipeline_name=yahboom_pick_and_place&signal_name=pick_red&priority=HIGH" -H "Content-Type: application/json"
```

## 前端设置

### 技术栈

- **Next.js**：具有服务器端渲染的 React 框架
- **TypeScript**：类型安全的 JavaScript
- **Tailwind CSS**：实用性优先的 CSS 框架
- **Shadcn/UI**：高质量、可访问的 UI 组件
- **React Query**：数据获取和状态管理
- **Jotai**：轻量级状态管理

### 架构

- **后端通信**：
  - REST API 用于基本操作（列出管道、启动/停止）
  - WebSocket 桥接用于实时更新和流传输
  - Redis 用于后端管道通信

- **UI 布局**：
  - 左侧边栏：用于管道设置的可折叠配置面板
  - 主区域：流帧和管道输出的可视化

### 安装

```bash
# 导航到前端目录
cd frontend

# 安装依赖项
bun install

# 运行开发服务器
bun run dev
```

### 构建

```bash
# 生产构建
bun run build

# 启动生产服务器
bun run start
```

### 功能

- 管道管理（列表、启动、停止）
- 信号控制，显示可用信号列表
- 实时管道状态监控
- 来自管道队列的实时帧可视化
- 适用于不同设备的响应式布局

## Git 钩子设置

该项目使用 git 钩子来确保代码质量和一致的提交消息。

### 设置钩子

1. 首先，在前端目录中准备 Husky 钩子：
   ```bash
   cd frontend
   bun run prepare:husky
   cd ..
   ```

2. 重置钩子路径以使用项目的自定义钩子：
   ```bash
   git config core.hooksPath .hooks
   ```

这个两步过程确保了前端和后端钩子都正确安装。第一个命令在前端目录中设置 Husky，但它也会将 git 钩子路径更改为 `frontend/.husky`。第二个命令将钩子路径重置为项目根目录的 `.hooks` 目录，其中包含整个项目的钩子。

### 钩子函数

- **pre-commit**：对前端和后端代码运行 lint 和格式化检查
- **commit-msg**：根据约定式提交格式验证提交消息

## 下一步

- **管道配置 UI**：添加用于修改管道配置的界面
- **增强可视化**：添加显示选项和多队列可视化的控件
- **用户认证**：添加基于角色的安全访问权限
- **额外的机器人模型**：支持不同的机械臂模型和配置
- **性能优化**：改进帧率控制和网络效率
- **实时分析**：添加指标和性能监控
