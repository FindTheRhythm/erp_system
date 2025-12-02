#!/bin/bash
# Скрипт для запуска миграций Alembic

echo "Running Alembic migrations..."
alembic upgrade head

echo "Migrations completed!"


