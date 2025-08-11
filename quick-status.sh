#!/bin/bash

# Quick Status Check Script
# This script provides a quick overview of all your services

echo "🚀 Quick Status Check for All Services..."

ssh aws << 'EOF'
echo "📊 SYSTEM OVERVIEW"
echo "=================="
echo "🕐 Server Time: $(date)"
echo "⚡ Uptime: $(uptime -p)"
echo "💾 Memory: $(free -h | grep Mem | awk '{print $3 "/" $2 " (" int($3/$2*100) "% used)"}')"
echo "💿 Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
echo

echo "🐳 DOCKER CONTAINERS STATUS"
echo "==========================="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -20
echo

echo "🔧 GO BACKEND API (Last 10 lines)"
echo "================================="
cd ~/oneline-inference-api 2>/dev/null && docker-compose logs --tail=10 backend 2>/dev/null | tail -10 || echo "⚠️  Backend logs not available"
echo

echo "🌐 REACT FRONTEND (Last 5 lines)"
echo "================================"
cd ~/oneline-react-app 2>/dev/null && docker-compose logs --tail=5 2>/dev/null | tail -5 || echo "⚠️  Frontend logs not available"
echo

echo "🎨 MOBART WORKER (Last 10 lines)"
echo "================================"
cd ~/mobart 2>/dev/null && docker-compose logs --tail=10 mobart-worker 2>/dev/null | tail -10 || echo "⚠️  Mobart worker logs not available"
echo

echo "🔧 REDIS STATUS"
echo "==============="
cd ~/oneline-inference-api 2>/dev/null
if docker-compose exec redis redis-cli --no-auth-warning -u redis://fE19y88N04mA26n:e15iN04SH19t93eIn@localhost:6379 ping >/dev/null 2>&1; then
    echo "✅ Redis is responding"
    echo "📊 Memory usage: $(docker-compose exec redis redis-cli --no-auth-warning -u redis://fE19y88N04mA26n:e15iN04SH19t93eIn@localhost:6379 info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')"
    echo "🔑 Total keys: $(docker-compose exec redis redis-cli --no-auth-warning -u redis://fE19y88N04mA26n:e15iN04SH19t93eIn@localhost:6379 dbsize)"
else
    echo "❌ Redis is not responding"
fi
echo

echo "🔍 RECENT ERRORS (if any)"
echo "========================"
echo "Checking for recent errors in all logs..."
cd ~ && docker logs --since="1h" $(docker ps -q) 2>&1 | grep -i error | tail -5 || echo "✅ No recent errors found"
echo

echo "✅ Quick status check completed!"
echo "💡 For detailed monitoring, run: ./monitor-services.sh"

EOF
