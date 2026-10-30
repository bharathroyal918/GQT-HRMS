#!/bin/sh
set -e
su - postgres -c "openssl req -new -x509 -days 365 -nodes -text -out /dev/shm/pgdata/server.crt -keyout /dev/shm/pgdata/server.key -subj '/CN=localhost'"
chmod 600 /dev/shm/pgdata/server.key
chown postgres:postgres /dev/shm/pgdata/server.crt /dev/shm/pgdata/server.key
echo "ssl = on" >> /dev/shm/pgdata/postgresql.conf
su - postgres -c "pg_ctl -D /dev/shm/pgdata reload"
