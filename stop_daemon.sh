#!/bin/bash

# News Bot Daemon Stopper
# 快速停止守护进程的脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 调用主daemon管理脚本
exec "$SCRIPT_DIR/start_daemon.sh" stop