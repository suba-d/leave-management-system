#!/bin/bash


if [ -z "$1"]; then
    echo "錯誤：需要提供commit message"
    echo "用法：./depoly.sh\"你的更新說名\""
    exit 1
fi



git add .
git commit -m "$1"
git push origin main

ssh root@35.72.237.247 "cd leave-management-system && git pull origin main"

