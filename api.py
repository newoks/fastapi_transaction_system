import json

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from db import models, crud
from db.database import SessionLocal, engine
from config.config import read_config
from rabbit.rabbitmq import RabbitPublisher

models.Base.metadata.create_all(bind=engine)
conf = read_config('config/config.yml')

app = FastAPI()


def get_pg_session():
    pg_session = SessionLocal()
    try:
        yield pg_session
    finally:
        pg_session.close()


@app.post('/transaction')  # Endpoint, реализующий транзакцию
def transaction(user_id_from: int, user_id_to: int, value: int,
                pg_session: Session = Depends(get_pg_session)):

    user_balance_from = crud.get_balance(pg_session, user_id=user_id_from)
    user_balance_to = crud.get_balance(pg_session, user_id=user_id_to)
    if user_balance_from is None or user_balance_to is None:  # Проверка существования пользователей
        raise HTTPException(status_code=404, detail="User not found")
    if user_balance_from.value < value:  # Проверка необходимого баланса для транзакции
        raise HTTPException(status_code=400, detail="Not enough money")

    # Подготавливаем два сообщения для очередей
    msg_from = {'value': value, 'type': 'from', 'second_user': user_id_to}
    msg_to = {'value': value, 'type': 'to', 'second_user': user_id_from}

    # Создаем publisher и отправляем два сообщения
    r_publisher = RabbitPublisher(config=conf)
    r_publisher.send(msg=json.dumps(msg_from), q=f'user_{user_id_from}')  # q = имя очереди
    r_publisher.send(msg=json.dumps(msg_to), q=f'user_{user_id_to}')  # для каждого пользователя своя очередь

    return 'OK'


if __name__ == '__main__':
    uvicorn.run(app, port=8080, host='localhost')
