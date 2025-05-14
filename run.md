启动四个脚本：


mac：
- backend
  - cd backend/ ; src .venv/bin/activate
  - uv sync
  - python main.py

- frontend
  - bun install
  - bun run dev


linux：
- 视频流发送端
  - cd backend/ ; src .venv/bin/activate
  - python -m examples.streaming --server 192.168.1.37  --source webcam:0 --keep_size --enable_freeze --visualization --time-window 0.1

- 机械臂接受命令端
  - cd ~/Work/Projects/scripts
  - python Server_280.py



操作流程：
1. 