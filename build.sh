#!/usr/bin/env bash

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

make install
psql -a -d $DATABASE_URL -f database.sql