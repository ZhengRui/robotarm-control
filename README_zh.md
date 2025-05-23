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

### Redis 服务器设置

Redis 是数据流传输和管道通信所必需的。按照以下步骤安装和配置 Redis：

1. **安装 Redis**：

   **Ubuntu/Debian 系统**：
   ```bash
   sudo apt update
   sudo apt install redis-server
   ```

   **macOS 系统**：
   ```bash
   brew install redis
   ```

   **Windows 系统**：
   通过 Windows Subsystem for Linux (WSL) 安装或从 [Redis for Windows](https://github.com/microsoftarchive/redis/releases) 下载。

2. **启动 Redis**：

   **Ubuntu/Debian 系统**：
   ```bash
   sudo systemctl start redis-server
   ```

   **macOS 系统**：
   ```bash
   brew services start redis
   ```

   **Windows 系统**：
   运行 redis-server.exe 应用程序。

3. **验证安装**：
   ```bash
   redis-cli ping
   ```

   您应该收到 `PONG` 响应。

4. **配置 Redis 允许远程连接**（可选，仅当从其他机器访问 Redis 时需要）：

   编辑 Redis 配置文件：

   **Ubuntu/Debian 系统**：
   ```bash
   sudo nano /etc/redis/redis.conf
   ```

   **macOS 系统**：
   ```bash
   nano $(brew --prefix)/etc/redis.conf
   ```

   进行以下更改：
   - 将 `bind 127.0.0.1` 更改为 `bind 0.0.0.0` 以允许来自任何 IP 的连接
   - 设置 `protected-mode no` 以禁用保护模式（Redis 6.0 及更新版本需要）
   - 可选，通过取消注释 `requirepass` 行并添加强密码来设置密码

   保存并重启 Redis：

   **Ubuntu/Debian 系统**：
   ```bash
   sudo systemctl restart redis-server
   ```

   **macOS 系统**：
   ```bash
   brew services restart redis
   ```

   如果您设置了密码，请记得在环境配置文件中更新 Redis 连接设置。

5. 项目中的默认配置使用 localhost:6379。如果需要更改这些设置，请在环境配置文件中更新。

### 远程机器人控制设置

**此设置仅在机械臂连接到与运行后端服务器的机器不同的机器时才需要**。如果您的机械臂直接连接到运行后端的机器，可以跳过此部分。

如果您使用远程机器人控制配置（在配置文件中设置了 `remote_addr`）：

1. **下载 Server_280.py 脚本**：

   从以下位置下载 MyCobot280 远程控制服务器脚本：
   ```
   https://github.com/modulus-inc/modulus-robotarm-control/blob/main/demo/Server_280.py
   ```

2. **在远程机器上运行脚本**：

   远程机器需要物理连接到机械臂。
   ```bash
   # 在远程机器上
   python Server_280.py
   ```

3. **配置您的环境**：

   确保您的 `dev.yaml` 或 `prod.yaml` 文件中将 `remote_addr` 设置为远程机器的 IP 地址。
   ```yaml
   # 配置示例
   handlers:
     robot_control:
       init:
         remote_addr: "192.168.1.100"  # 远程机器的 IP 地址
   ```

这种设置使后端能够将控制命令发送到直接连接到机械臂的远程机器。

### 启动后端服务器

启动服务器：

```bash
python main.py
```

您可以指定环境和初始管道：

```bash
ENV=dev PIPELINE=yahboom_pick_and_place python main.py
```

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

## 运行流媒体客户端

后端系统设计用于处理图像帧，但它需要数据源才能操作。一旦后端服务器运行起来，它会等待流数据输入，然后管道才能处理有意义的内容。

要将数据流传输到系统：

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

### 完整数据流

运行完整系统时：

1. **流媒体客户端**从摄像头或视频文件捕获帧并将其发送到 Redis
2. **后端管道**通过其 DataLoaderHandler 接收这些帧
3. **管道处理器**处理帧（检测、控制计算等）
4. **前端仪表板**通过以下方式连接到后端：
   - REST API 用于管道操作（启动/停止）
   - WebSocket 用于实时更新和帧数据

使用此设置，您可以：
- 从仪表板启动管道
- 发送控制信号以更改管道行为
- 实时可视化流帧和处理结果
- 查看机械臂响应检测到的物体

前端连接到每个管道的发布队列，使您能够监控管道"看到"的内容以及它如何处理数据。

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

## 实现自定义管道

Modulus 机械臂控制系统设计为可通过自定义管道扩展。以下是实现自己的管道的方法：

### 1. 创建新的管道模块

在 `backend/lib/pipelines/` 下为您的管道创建一个新目录：

```
backend/lib/pipelines/my_custom_pipeline/
├── __init__.py
├── config.yaml
├── handlers/
│   ├── __init__.py
│   └── custom_handler.py
└── pipeline.py
```

### 2. 实现您的管道类

创建一个实现管道状态机的 `pipeline.py` 文件：

<details>
<summary>点击展开代码: pipeline.py</summary>

```python
from typing import Dict, List, Optional, Any, Set
import json
from enum import Enum, auto
from pydantic import BaseModel

from ...utils.logger import get_logger
from ..base import BasePipeline

logger = get_logger("my_custom_pipeline")

class PipelineState(str, Enum):
    """管道状态枚举。"""
    IDLE = "IDLE"
    INIT = "INIT"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"

class PipelineSignal(str, Enum):
    """管道信号枚举。"""
    START = "start"
    STOP = "stop"
    RESET = "reset"

class PipelineQueue(str, Enum):
    """管道队列枚举。"""
    FRAMES = "frames"
    DEBUG = "debug"

class CustomConfigSchema(BaseModel):
    """管道配置验证的模式。"""
    parameter1: str
    parameter2: int

class Pipeline(BasePipeline):
    """自定义管道实现。"""

    def __init__(self, pipeline_name: str) -> None:
        """初始化管道。

        参数:
            pipeline_name: 管道实例的名称
        """
        super().__init__(pipeline_name)

        # 定义当前状态
        self._current_state = PipelineState.IDLE

    @property
    def current_state(self) -> str:
        """获取管道的当前状态。

        返回:
            当前状态的字符串表示
        """
        return self._current_state.value

    @classmethod
    def get_available_signals(cls) -> List[str]:
        """获取可用信号列表。

        返回:
            信号名称列表
        """
        return [signal.value for signal in PipelineSignal]

    @classmethod
    def get_available_states(cls) -> List[str]:
        """获取可能的管道状态列表。

        返回:
            状态名称列表
        """
        return [state.value for state in PipelineState]

    @classmethod
    def get_available_queues(cls) -> List[str]:
        """获取可用数据队列列表。

        返回:
            队列名称列表
        """
        return [queue.value for queue in PipelineQueue]

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """获取此管道的配置模式。

        返回:
            作为字典的配置模式
        """
        return CustomConfigSchema.schema()

    def handle_signal(self, signal_name: str, **kwargs: Any) -> None:
        """处理传入的信号。

        参数:
            signal_name: 要处理的信号名称
            **kwargs: 附加的信号参数
        """
        logger.info(f"处理信号: {signal_name}")

        if signal_name == PipelineSignal.START.value and self._current_state == PipelineState.IDLE:
            self._current_state = PipelineState.INIT
        elif signal_name == PipelineSignal.STOP.value:
            self._current_state = PipelineState.IDLE
        elif signal_name == PipelineSignal.RESET.value:
            self._current_state = PipelineState.IDLE
            # 在此重置任何管道状态

    def step(self) -> None:
        """根据当前状态执行单个管道步骤。"""
        if self._current_state == PipelineState.IDLE:
            # 在 IDLE 状态下不做任何事情
            pass

        elif self._current_state == PipelineState.INIT:
            logger.info("初始化管道")
            # 执行初始化任务
            self._current_state = PipelineState.RUNNING

        elif self._current_state == PipelineState.RUNNING:
            # 从数据加载器处理器获取数据
            data_loader = self.handlers.get("data_loader")
            if data_loader:
                # 从配置获取处理参数
                data_loader_params = self.config.get("handlers", {}).get("data_loader", {}).get("process", {})
                result = data_loader.process(**data_loader_params)

                frame = None
                if result and "frame" in result:
                    frame = result["frame"]

                if frame is None:
                    return

                # 使用自定义处理器处理帧
                custom_handler = self.handlers.get("custom_handler")
                if custom_handler:
                    # 获取自定义处理器处理参数
                    custom_handler_params = self.config.get("handlers", {}).get("custom_handler", {}).get("process", {})
                    result = custom_handler.process(frame=frame, **custom_handler_params)

                    # 如果启用了调试模式，发布调试可视化
                    debug_image = result.get("debug_image")
                    if debug_image is not None:
                        self.publish_to_queue(
                            PipelineQueue.DEBUG.value,
                            base64.b64encode(debug_image.tobytes()).decode("utf-8") # 假设 debug_image 是 ndarray/cvimage
                        )

                    # 检查完成条件
                    if result.get("status") == "complete":
                        self._current_state = PipelineState.COMPLETE

                # 始终将原始帧发布到 frames 队列
                self.publish_to_queue(
                    PipelineQueue.FRAMES.value,
                    base64.b64encode(frame.tobytes()).decode("utf-8") # 假设 frame 是 ndarray/cvimage
                )

        elif self._current_state == PipelineState.COMPLETE:
            logger.info("管道执行完成")
            self._current_state = PipelineState.IDLE
```

</details>

### 3. 创建管道配置

为您的管道的默认配置定义一个 `config.yaml` 文件：

<details>
<summary>点击展开代码: config.yaml</summary>

```yaml
Pipeline:
  # Redis 设置
  redis:
    host: "localhost"
    port: 6379
    db: 0
    password: null

  # 处理器配置
  handlers:
    data_loader:
      init:
        backend: "redis"  # 将使用上面 redis 块中的 redis 设置
      process:
        wait: false

    custom_handler:
      init:
        parameter1: "value1"
        parameter2: 42
      process:
        debug: false
```

</details>

### 4. 实现自定义处理器

在 `handlers` 目录中创建您的自定义处理器：

<details>
<summary>点击展开代码: custom_handler.py</summary>

```python
# custom_handler.py
from typing import Any, Dict

from ....handlers.base import BaseHandler

class CustomHandler(BaseHandler):
    """自定义处理处理器。"""

    def __init__(self, parameter1: str = "", parameter2: int = 0) -> None:
        """初始化处理器。

        参数:
            parameter1: 第一个参数
            parameter2: 第二个参数
        """
        self.parameter1 = parameter1
        self.parameter2 = parameter2

    def process(self, frame: Any = None, debug: bool = False) -> Dict[str, Any]:
        """处理输入帧。

        参数:
            frame: 要处理的输入帧
            debug: 启用调试模式以可视化处理步骤

        返回:
            处理结果
        """
        # 在此实现您的自定义处理逻辑
        result = {
            "data": None
        }

        # 示例处理
        if frame is not None:
            # 对帧做一些操作
            # ...
            result["data"] = "已处理的数据"

            # 可选的调试可视化
            if debug:
                # 创建用于监控的调试可视化
                result["debug_image"] = frame  # 示例：返回可视化帧

        return result
```

</details>

### 5. 注册处理器

在您的管道模块的 `__init__.py` 中，注册处理器：

```python
from ...handlers import HandlerFactory
from .handlers.custom_handler import CustomHandler
from .pipeline import Pipeline

# 为此管道注册自定义处理器
HandlerFactory.register_for_pipeline(Pipeline, "custom_handler", CustomHandler)

__all__ = ["Pipeline", "CustomHandler"]
```

### 6. 注册管道

在主 `backend/lib/pipelines/__init__.py` 文件中，注册您的管道：

```python
# 添加您的导入
from .my_custom_pipeline import Pipeline as MyCustomPipeline

# 添加您的管道注册
PipelineFactory.register_pipeline("my_custom_pipeline", MyCustomPipeline)

# 更新 __all__ 以包含您的管道
__all__ = [
    "BasePipeline",
    "PipelineFactory",
    "SignalPriority",
    "YahboomPickAndPlacePipeline",
    "ModulusPipeline",
    "MyCustomPipeline",  # 添加此行
]
```

### 7. 将管道添加到环境配置

将您的管道添加到您的环境配置文件中（例如，`backend/config/dev.yaml`）：

```yaml
# 现有管道
yahboom_pick_and_place:
   pipeline: yahboom_pick_and_place

# 您的新管道
my_custom_pipeline:
   pipeline: my_custom_pipeline
   # 环境特定的覆盖
   handlers:
   custom_handler:
      init:
         parameter1: "custom_value"
```

### 8. 使用您的自定义管道

实现后，您可以通过 API 使用您的管道：

```bash
# 启动您的自定义管道
curl -X POST "http://localhost:8000/pipeline/start?pipeline_name=my_custom_pipeline"

# 向您的管道发送信号
curl -X POST "http://localhost:8000/pipeline/signal?pipeline_name=my_custom_pipeline&signal_name=start"
```

或者在服务器启动时自动启动：

```bash
ENV=dev PIPELINE=my_custom_pipeline python main.py
```

这个框架允许您专注于实现管道的特定业务逻辑，同时利用现有的基础设施进行流程管理、配置和 API 集成。

## 下一步

- **管道配置 UI**：添加用于修改管道配置的界面
