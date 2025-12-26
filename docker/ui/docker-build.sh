#!/usr/bin/env bash

cd ../..

docker build -t arina/sber/dashboard-ui:main -f docker/ui/Dockerfile .
