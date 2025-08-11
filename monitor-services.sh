#!/bin/bash

# Monitor Services Script
# This script connects to your EC2 server and monitors all your applications

echo "🚀 Starting service monitoring for all applications..."

# SSH into your EC2 server and create a comprehensive monitoring session
ssh aws << 'EOF'
# Kill existing monitoring session if it exists
tmux kill-session -t monitoring 2>/dev/null || true

# Create new tmux session called "monitoring"
tmux new-session -d -s monitoring -x 120 -y 40

# Window 1: Backend API Logs
tmux rename-window -t monitoring:0 "Backend-API"
tmux send-keys -t monitoring:0 "cd ~/oneline-inference-api && echo '🔧 Go Backend API Logs:' && docker-compose logs -f --tail=50 backend" Enter

# Window 2: Frontend Logs  
tmux new-window -t monitoring -n "Frontend-Web"
tmux send-keys -t monitoring:1 "cd ~/oneline-react-app && echo '🌐 React Frontend Logs:' && docker-compose logs -f --tail=50" Enter

# Window 3: Mobart Worker Logs
tmux new-window -t monitoring -n "Mobart-Worker"
tmux send-keys -t monitoring:2 "cd ~/mobart && echo '🎨 Mobart Worker Logs:' && docker-compose logs -f --tail=50 mobart-worker" Enter

# Window 4: System Monitoring (split into multiple panes)
tmux new-window -t monitoring -n "System-Monitor"

# Top pane: htop
tmux send-keys -t monitoring:3 "echo '💻 System Resources (htop):' && htop" Enter

# Split horizontally
tmux split-window -t monitoring:3 -v

# Bottom left pane: Docker stats
tmux send-keys -t monitoring:3.1 "echo '🐳 Docker Container Stats:' && watch -n 2 'docker stats --no-stream'" Enter

# Split bottom pane vertically
tmux split-window -t monitoring:3.1 -h

# Bottom right pane: Disk usage and system info
tmux send-keys -t monitoring:3.2 "echo '📊 System Overview:' && watch -n 5 'echo \"=== DISK USAGE ===\" && df -h && echo && echo \"=== MEMORY USAGE ===\" && free -h && echo && echo \"=== LOAD AVERAGE ===\" && uptime && echo && echo \"=== ACTIVE CONTAINERS ===\" && docker ps --format \"table {{.Names}}\t{{.Status}}\t{{.Ports}}\"'" Enter

# Window 5: All Logs Combined
tmux new-window -t monitoring -n "All-Logs"
tmux send-keys -t monitoring:4 "echo '📋 Combined Logs from All Services:' && echo" Enter
tmux send-keys -t monitoring:4 "cd ~ && docker logs --tail=20 -f \$(docker ps -q) 2>/dev/null || echo 'Monitoring all container logs...'" Enter

# Window 6: Redis Monitoring
tmux new-window -t monitoring -n "Redis-Monitor"
tmux send-keys -t monitoring:5 "echo '🔧 Redis Monitoring:' && cd ~/oneline-inference-api" Enter
tmux send-keys -t monitoring:5 "watch -n 2 'echo \"=== REDIS INFO ===\" && docker-compose exec redis redis-cli --no-auth-warning -u redis://fE19y88N04mA26n:e15iN04SH19t93eIn@localhost:6379 info memory | head -10 && echo && echo \"=== REDIS KEYS ===\" && docker-compose exec redis redis-cli --no-auth-warning -u redis://fE19y88N04mA26n:e15iN04SH19t93eIn@localhost:6379 keys \"*\" | head -10'" Enter

# Set default window to Backend
tmux select-window -t monitoring:0

echo
echo "✅ Tmux monitoring session created successfully!"
echo "📊 Available windows:"
echo "   0: Backend-API     - Go backend logs"
echo "   1: Frontend-Web    - React frontend logs" 
echo "   2: Mobart-Worker   - Python worker logs"
echo "   3: System-Monitor  - htop, docker stats, system info"
echo "   4: All-Logs        - Combined logs from all services"
echo "   5: Redis-Monitor   - Redis stats and keys"
echo
echo "🎯 Navigation:"
echo "   Ctrl+b + [0-5]     - Switch between windows"
echo "   Ctrl+b + arrow     - Switch between panes"
echo "   Ctrl+b + d         - Detach session (keeps running)"
echo "   exit               - Close current pane/window"
echo
echo "🔄 To reconnect later: tmux attach -t monitoring"

# Attach to the session
tmux attach -t monitoring

EOF

echo "👋 Monitoring session ended."
