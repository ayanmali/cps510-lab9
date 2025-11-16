#!/bin/bash

uv pip freeze > requirements.txt
docker build -t cps510-lab9 .