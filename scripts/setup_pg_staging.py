import psycopg

def setup_staging():
    admin_conn = psycopg.connect("postgresql://postgres@localhost:5432/postgres", autocommit=True)
    with admin_conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'gqt_hrms_staging'")
        if cur.fetchone():
            print("Terminating existing connections to gqt_hrms_staging...")
            cur.execute("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'gqt_hrms_staging' AND pid <> pg_backend_pid()
            """)
            cur.execute("DROP DATABASE gqt_hrms_staging")
            print("Dropped previous gqt_hrms_staging database.")

        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'gqt_hrms_app'")
        if not cur.fetchone():
            cur.execute("CREATE ROLE gqt_hrms_app WITH LOGIN PASSWORD 'gqt_staging_password_secure'")
            print("Created role gqt_hrms_app.")

        cur.execute("CREATE DATABASE gqt_hrms_staging OWNER gqt_hrms_app")
        cur.execute("GRANT ALL PRIVILEGES ON DATABASE gqt_hrms_staging TO gqt_hrms_app")
        print("Created database gqt_hrms_staging with owner gqt_hrms_app.")
    admin_conn.close()

    # Verify non-superuser connection
    app_conn = psycopg.connect("postgresql://gqt_hrms_app:gqt_staging_password_secure@localhost:5432/gqt_hrms_staging")
    with app_conn.cursor() as cur:
        cur.execute("SELECT current_user, current_database(), usesuper FROM pg_user WHERE usename = current_user;")
        row = cur.fetchone()
        print("Verified least-privilege app user:", row)
        assert row[2] is False, "Application user MUST NOT be superuser!"
    app_conn.close()

if __name__ == "__main__":
    setup_staging()
