from typing import Optional, Dict, Any

import pika
from pika.exceptions import ChannelClosedByBroker, ConnectionClosedByBroker


class RabbitConnection:

    def __init__(self, config: Dict[str, Any], queue: str = None):
        """
        :param config: Конфиг подключения к Rabbit
        :param queue: Имя очереди
        """
        self.channel = None
        self.connection = None
        self.config = config
        self.queue = queue
        self._init_connection()

    def _try_init_connection(self):
        try:
            self._init_connection()
        except Exception as e:
            print(f'RABBITMQ INIT CONNECTION FAILED: {e}')

    def _init_connection(self):
        credentials = pika.PlainCredentials(self.config['rabbitmq']['user'], self.config['rabbitmq']['password'])
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.config['rabbitmq']['host'],
                                      port=self.config.get('port', 5672),
                                      credentials=credentials))
        self.channel = self.connection.channel()
        if self.queue:
            try:
                self.channel.queue_declare(queue=self.queue, durable=True)
            except ChannelClosedByBroker as e:
                if 'PRECONDITION_FAILED' in str(e):
                    print(f'RabbitMQ init warning: probably queue {self.queue} already exists. Skip declare')
                self.channel = self.connection.channel()

    @property
    def _connection_is_closed(self):
        try:
            if not (self.connection and self.channel):
                return True
            if self.channel.is_closed or self.connection.is_closed:
                return True
            self.connection.sleep(0.01)  # Ping: https://github.com/pika/pika/issues/877
            return False
        except ConnectionError:
            return True
        except ConnectionClosedByBroker:
            return True
        except Exception as e:
            print(f'Unknown rabbit ping error: {e}')
            return True

    def ping(self):
        return not self._connection_is_closed


class RabbitPublisher(RabbitConnection):
    # Класс для отправки одного сообщения в очередь

    def send(self, msg: bytes, q: str):
        """
        Отправка одного сообщения в очередь
        :param q: название очереди
        :param msg: Тело сообщения
        """
        self._init_connection()  # Создаем новое подключение к очереди каждый раз
        self.channel.basic_publish(exchange='', routing_key=q, body=msg,
                                   properties=pika.BasicProperties(delivery_mode=2))  # Persistent сообщение
        print('sent msg', msg, q)
        self.connection.close()


class RabbitConsumer(RabbitConnection):
    # Единовременно один экземпляр RabbitConsumer может обрабатывать только одно сообщение
    # Алгоритм: get_one_message -> remember delivery_tag -> ack delivery_tag -> get_one_message -> ...
    current_delivery_tag = None

    def get_one_message(self) -> Optional[bytes]:
        """
        Получение нового сообщения
        Не может быть получено раньше, чем ack'нуто предыдущее
        :return: Тело сообщения
        """
        if self.current_delivery_tag:
            raise ValueError(f"Rabbit current_delivery_tag not empty: {self.current_delivery_tag}. Can't get new "
                             f'message')
        if self._connection_is_closed:
            print('Reconnecting to rabbit %s/%s to get message' % (self.config['host'], self.queue))
            self._init_connection()
        method_frame, message_properties, body = self.channel.basic_get(self.queue, auto_ack=False)
        if method_frame:  # В очереди нет сообщений, подождем еще немного
            self.current_delivery_tag = method_frame.delivery_tag
            return body

    def ack(self) -> None:
        """
        Уведомление об успешной обработке последнего полученного сообщения
        """
        if self._connection_is_closed:
            self._init_connection()
            print('Reconnecting to rabbit %s/%s to ack message' % (self.config['host'], self.queue))
        self.channel.basic_ack(self.current_delivery_tag)
        self.current_delivery_tag = None


class RabbitEndlessConsumer(RabbitConsumer):

    def get_one_message(self) -> Optional[bytes]:
        while True:
            if msg := super().get_one_message():
                return msg
            self.connection.sleep(0.05)