from fastapi import FastAPI
from sqlmodel import create_engine, Session, SQLModel, select

from models.config_item import KeyValue

app = FastAPI()
engine = create_engine("sqlite:///database.db")


@app.get("/ping")
async def ping():
    return {"message": "pong"}


# @app.get("/key_value/{project_id}/{key}")
# async def get_key_value(project_id: str, key: str):
#     with Session(engine) as session:
#         item = session.exec(KeyValue).filter(KeyValue.key == key).first()

#         print(type(item))
#         if item:
#             return {"key": item.key, "value": item.value}
#         else:
#             return {"error": "Key not found"}, 404


@app.get("/key_value/{project_id}")
async def get_all_key_values(project_id: str):
    with Session(engine) as session:
        statement = select(KeyValue).where(KeyValue.project_id == project_id)
        results = session.exec(statement)

        return [{"key": item.key, "value": item.value} for item in results]


@app.post("/key_value")
async def create_key_value(item: KeyValue):
    with Session(engine) as session:
        session.add(item)
        session.commit()
        session.refresh(item)
        return {"key": item.key, "value": item.value}
