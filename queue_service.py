import json

from db.database import SessionLocal
from db.crud import *
from rabbit.rabbitmq import RabbitConsumer, RabbitPublisher
from config.config import read_config

pg_session = SessionLocal()
conf = read_config('config/config.yml')


# Функция для изменения баланса пользователей
def update_balance_for_user(user_id: int, value: int, type: str,
                            pg_session: Session):
    user_balance = get_balance(pg_session=pg_session, user_id=user_id)

    if type == 'from':  # При помощи условия узнаем, нужно отнять или прибавить value
        updated_balance = models.Balance(user_id=user_id, value=user_balance.value - value)
        pg_session.add(updated_balance)
    elif type == 'to':
        updated_balance = models.Balance(user_id=user_id, value=user_balance.value + value)
        pg_session.add(updated_balance)

    pg_session.flush()


# Цикл, который постоянно считывает сообщения из очереди и изменяет баланс
while True:
    users = get_users(pg_session=pg_session)  # Получаем всех пользователей

    for user in users:  # и проверяем в цикле для кого из них есть сообщения в очереди
        r_consumer = RabbitConsumer(config=conf, queue=f'user_{user.id}')
        body = r_consumer.get_one_message()

        if body is None:  # Если для пользователя есть сообщение
            continue
        body = json.loads(body)  # сохраняем ответ

        if isinstance(body, str):  # почему-то body иногда приходит в формате str, надо изменить
            body = json.loads(body)

        try:  # Обновляем баланс пользователя
            update_balance_for_user(pg_session=pg_session, user_id=user.id, value=body['value'], type=body['type'])

        except Exception as e:  # Если не удалось (например упал сервер)
            print(str(e))
            pg_session.rollback() # в случае ошибки посылаем в Rabbit инвертированный меседж
            RabbitPublisher(config=conf).send(msg=json.dumps(dict(value=body['value'], type=body['type'])),
                                              q=f'user_{body["second_user"]}')
        else:  # Если все ок, коммитим в базу
            pg_session.commit()

        finally:  # И в любом случае аск'аем это сообщение
            r_consumer.ack()
