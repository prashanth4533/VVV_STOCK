from sqlalchemy import inspect, text

from app import create_app, db


def main():
    app = create_app()
    with app.app_context():
        engine = db.engine
        if engine.url.get_backend_name() != "mysql":
            raise RuntimeError(f"Expected MySQL, got {engine.url.get_backend_name()}")

        with engine.connect() as conn:
            database_name = conn.execute(text("SELECT DATABASE()")).scalar()
            print(f"database={database_name}")

            inspector = inspect(conn)
            tables = inspector.get_table_names()
            print("tables=" + ",".join(tables))

            for table in tables:
                quoted = f"`{table.replace('`', '``')}`"
                count = conn.execute(text(f"SELECT COUNT(*) FROM {quoted}")).scalar()
                print(f"{table}={count}")


if __name__ == "__main__":
    main()
