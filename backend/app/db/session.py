from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./db.sqlite3"

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    try:
        SQLModel.metadata.create_all(engine)
        print("Database and tables created.")
    except OperationalError as e:
        print(f"Error creating database and tables: {e}")