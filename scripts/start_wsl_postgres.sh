#!/bin/sh
set -e
mkdir -p /var/lib/postgresql/data /run/postgresql
chown -R postgres:postgres /run/postgresql

if ! mount | grep -q "/var/lib/postgresql/data"; then
    mount -t tmpfs -o size=1G tmpfs /var/lib/postgresql/data
fi
chown -R postgres:postgres /var/lib/postgresql /run/postgresql

if [ ! -f /var/lib/postgresql/data/PG_VERSION ]; then
    su - postgres -c "initdb -D /var/lib/postgresql/data --encoding=UTF8 --locale=C"
    echo "listen_addresses = '*'" >> /var/lib/postgresql/data/postgresql.conf
    echo "host all all 0.0.0.0/0 trust" >> /var/lib/postgresql/data/pg_hba.conf
    echo "host all all ::0/0 trust" >> /var/lib/postgresql/data/pg_hba.conf
fi

su - postgres -c "pg_ctl -D /var/lib/postgresql/data -l /var/lib/postgresql/data/server.log status" || \
su - postgres -c "pg_ctl -D /var/lib/postgresql/data -l /var/lib/postgresql/data/server.log start"

sleep 2
su - postgres -c "pg_isready"
