#!/bin/bash

exec uvicorn app.app:app --reload
