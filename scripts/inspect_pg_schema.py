import psycopg

def inspect_schema():
    conn = psycopg.connect("postgresql://gqt_hrms_app:gqt_staging_password_secure@localhost:5432/gqt_hrms_staging?sslmode=require")
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
    table_count = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM pg_constraint WHERE contype = 'f';")
    fk_count = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM pg_constraint WHERE contype = 'p';")
    pk_count = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM pg_constraint WHERE contype = 'u';")
    unique_count = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM pg_constraint WHERE contype = 'c';")
    check_count = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM pg_indexes WHERE schemaname = 'public';")
    index_count = cur.fetchone()[0]

    print(f"TABLES: {table_count}")
    print(f"PRIMARY KEYS: {pk_count}")
    print(f"FOREIGN KEYS: {fk_count}")
    print(f"UNIQUE CONSTRAINTS: {unique_count}")
    print(f"CHECK CONSTRAINTS: {check_count}")
    print(f"INDEXES: {index_count}")

    # Inspect critical tables
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]
    print("\nSAMPLE TABLES (total {}):".format(len(tables)))
    for t in tables[:15]:
        print(f" - {t}")
    print(" ... and {} more".format(len(tables) - 15))

    conn.close()

if __name__ == "__main__":
    inspect_schema()
