"""
Клиент для работы с RabbitMQ
"""
import pika
import json
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """Клиент для публикации событий в RabbitMQ"""
    
    _connection: Optional[pika.BlockingConnection] = None
    _channel: Optional[pika.channel.Channel] = None
    
    def __init__(self):
        # Не подключаемся при инициализации, только при первом использовании
        pass
    
    def _connect(self):
        """Установить соединение с RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                settings.RABBITMQ_USER,
                settings.RABBITMQ_PASSWORD
            )
            parameters = pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=credentials
            )
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            
            # Объявить exchange для событий
            self._channel.exchange_declare(
                exchange='erp_events',
                exchange_type='topic',
                durable=True
            )
            
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            self._connection = None
            self._channel = None
    
    def _ensure_connection(self):
        """Убедиться что соединение активно"""
        if self._connection is None or self._connection.is_closed:
            self._connect()
    
    def publish_event(self, event_type: str, data: dict):
        """Отправить событие в RabbitMQ"""
        try:
            self._ensure_connection()
            
            if self._channel is None:
                logger.error("RabbitMQ channel is not available")
                return
            
            message = json.dumps(data)
            
            self._channel.basic_publish(
                exchange='erp_events',
                routing_key=f'inventory.{event_type}',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Сохранять сообщение на диск
                )
            )
            
            logger.info(f"Published event: inventory.{event_type}")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
    
    def close(self):
        """Закрыть соединение"""
        if self._connection and not self._connection.is_closed:
            self._connection.close()


# Глобальный экземпляр клиента
rabbitmq_client = RabbitMQClient()

