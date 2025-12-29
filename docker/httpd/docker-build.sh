#!/usr/bin/env bash

cd ../..

docker build -t arina/sber/httpd:2.4 -f docker/httpd/Dockerfile .
