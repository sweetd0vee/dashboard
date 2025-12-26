#!/usr/bin/env bash

cd ../..

docker build -t arina/aiops/postgres:16.9-bookworm -f docker/postgres/Dockerfile .
