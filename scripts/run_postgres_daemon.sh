#!/bin/sh
set -e
mkdir -p /dev/shm/pgdata /run/postgresql
chown -R postgres:postgres /dev/shm/pgdata /run/postgresql
chmod 777 /run/postgresql

if [ ! -f /dev/shm/pgdata/PG_VERSION ]; then
    echo "Initializing PostgreSQL cluster..."
    su - postgres -c "initdb -D /dev/shm/pgdata --encoding=UTF8 --locale=C"
    echo "listen_addresses = '*'" >> /dev/shm/pgdata/postgresql.conf
    echo "host all all 0.0.0.0/0 trust" >> /dev/shm/pgdata/pg_hba.conf
    echo "host all all ::0/0 trust" >> /dev/shm/pgdata/pg_hba.conf
fi

echo "Starting postgres server in foreground..."
exec su - postgres -c "postgres -D /dev/shm/pgdata"
