#!/bin/bash

git add .
git commit -m "$1"
git push origin main

ssh root@35.72.237.247 "cd leave-management-system && git pull origin main"

