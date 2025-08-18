#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}🚀 開始部署請假系統...${NC}"

# 檢查是否有提供commit message
if [ -z "$1" ]; then
    echo -e "${RED}❌ 請提供commit message${NC}"
    echo "用法: ./deploy.sh \"你的更新說明\""
    exit 1
fi

# Git操作
echo "📦 推送程式碼到GitHub..."
if git add . && git commit -m "$1" && git push origin main; then
    echo -e "${GREEN}✅ 程式碼已推送${NC}"
else
    echo -e "${RED}❌ Git推送失敗${NC}"
    exit 1
fi

# 部署到EC2
echo "🔄 部署到EC2..."
if ssh root@35.72.237.247 "cd leave-management-system && git pull origin main && systemctl restart leave-management.service"; then
    echo -e "${GREEN}✅ 部署成功！${NC}"
else
    echo -e "${RED}❌ 部署失敗${NC}"
    exit 1
fi
