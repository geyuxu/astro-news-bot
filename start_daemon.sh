#!/bin/bash

# News Bot Daemon Starter
# 真正的后台守护进程启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PID_FILE="$SCRIPT_DIR/news_scheduler.pid"
LOG_FILE="$LOG_DIR/daemon.log"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 函数：检查进程是否运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# 函数：启动守护进程
start_daemon() {
    if is_running; then
        echo "❌ Scheduler is already running (PID: $(cat $PID_FILE))"
        exit 1
    fi
    
    echo "🚀 Starting news scheduler daemon..."
    
    # 使用nohup启动守护进程，完全后台运行
    nohup python -m news_bot.scheduler start > "$LOG_FILE" 2>&1 &
    local nohup_pid=$!
    
    # 等待Python进程启动并创建自己的PID文件
    echo "⏳ Waiting for scheduler to initialize..."
    for i in {1..10}; do
        if [ -f "$PID_FILE" ]; then
            local python_pid=$(cat "$PID_FILE")
            if kill -0 "$python_pid" 2>/dev/null; then
                echo "✅ Scheduler daemon started successfully"
                echo "📋 Python PID: $python_pid"
                echo "📋 Wrapper PID: $nohup_pid"
                echo "📄 Log file: $LOG_FILE"
                echo "🛑 Stop with: ./stop_daemon.sh or python -m news_bot.scheduler stop"
                echo ""
                echo "📊 Status check:"
                sleep 1
                python -m news_bot.scheduler status
                return 0
            fi
        fi
        sleep 1
    done
    
    # 如果Python进程没有成功启动，清理nohup进程
    echo "❌ Failed to start scheduler daemon"
    if kill -0 "$nohup_pid" 2>/dev/null; then
        kill "$nohup_pid" 2>/dev/null || true
    fi
    echo "📄 Check log file: $LOG_FILE"
    exit 1
}

# 函数：停止守护进程
stop_daemon() {
    if ! is_running; then
        echo "ℹ️  Scheduler is not running"
        exit 0
    fi
    
    local pid=$(cat "$PID_FILE")
    echo "🛑 Stopping news scheduler daemon (PID: $pid)..."
    
    # 首先尝试优雅停止
    if kill -TERM "$pid" 2>/dev/null; then
        echo "⏳ Waiting for graceful shutdown..."
        
        # 等待进程停止
        for i in {1..15}; do
            if ! kill -0 "$pid" 2>/dev/null; then
                rm -f "$PID_FILE"
                echo "✅ Scheduler daemon stopped successfully"
                
                # 清理可能存在的nohup进程
                cleanup_related_processes
                return 0
            fi
            sleep 1
        done
        
        # 如果优雅停止失败，强制停止
        echo "⚠️  Graceful shutdown timeout, force stopping..."
        kill -KILL "$pid" 2>/dev/null || true
    else
        echo "⚠️  Process not responding, attempting force stop..."
        kill -KILL "$pid" 2>/dev/null || true
    fi
    
    # 清理PID文件和相关进程
    rm -f "$PID_FILE"
    cleanup_related_processes
    echo "✅ Scheduler daemon stopped (forced)"
}

# 函数：清理相关进程
cleanup_related_processes() {
    # 查找并清理可能残留的相关进程
    local related_pids=$(pgrep -f "python.*news_bot.scheduler" 2>/dev/null || true)
    if [ -n "$related_pids" ]; then
        echo "🧹 Cleaning up related processes: $related_pids"
        for pid in $related_pids; do
            kill -TERM "$pid" 2>/dev/null || true
        done
        
        # 等待一秒后强制清理
        sleep 1
        for pid in $related_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                kill -KILL "$pid" 2>/dev/null || true
            fi
        done
    fi
}

# 函数：重启守护进程
restart_daemon() {
    echo "🔄 Restarting news scheduler daemon..."
    stop_daemon
    sleep 2
    start_daemon
}

# 函数：显示状态
show_status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo "✅ Scheduler daemon is running (PID: $pid)"
        echo "📄 Log file: $LOG_FILE"
        echo ""
        python -m news_bot.scheduler status
    else
        echo "❌ Scheduler daemon is not running"
    fi
}

# 函数：显示日志
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "📄 Showing last 50 lines of daemon log:"
        echo "----------------------------------------"
        tail -n 50 "$LOG_FILE"
    else
        echo "❌ Log file not found: $LOG_FILE"
    fi
}

# 函数：显示帮助
show_help() {
    cat << EOF
🤖 News Bot Daemon Manager

USAGE:
    $0 [COMMAND]

COMMANDS:
    start       Start the scheduler daemon
    stop        Stop the scheduler daemon  
    restart     Restart the scheduler daemon
    status      Show daemon status
    logs        Show daemon logs (last 50 lines)
    help        Show this help message

EXAMPLES:
    $0 start            # 启动后台守护进程
    $0 stop             # 停止守护进程
    $0 status           # 查看运行状态
    $0 logs             # 查看运行日志

FILES:
    PID file: $PID_FILE
    Log file: $LOG_FILE
EOF
}

# 主逻辑
case "${1:-help}" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        restart_daemon
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac