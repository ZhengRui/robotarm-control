启动四个脚本：



Linux(nvidia)：
- clash
  - cd Work/Libs/clash
  - sudo ./restart.sh

- backend
  - cd backend/ ; src .venv/bin/activate
  <!-- - uv sync -->
  - python main.py

- frontend
  - cd frontend/ ;
  <!-- - bun install -->
  - bun run dev


- 视频流发送端
  - cd backend/ ; src .venv/bin/activate
  - python -m examples.streaming --server localhost  --source webcam:0 --keep_size --enable_freeze --visualization --time-window 0.1

<!-- - 机械臂接受命令端
  - cd ~/Work/Projects/scripts
  - python Server_280.py -->



操作流程：
1. localhost:3000 前段
2. 选择 yahboom_pick_and_stack ， toggle on， 左侧应该显示 calibrating
3. 右边 queue 选择 calibration_frames, detection_frames
4. 把标定纸（十字）对正（黑线对正），如果老是识别绿色外框最外层，就把手放进去一点。
5. 点击 calibration_confirmed，detection_frames显示十字在中间即可。
6. 可以把纸拿开
7. pick_stack


