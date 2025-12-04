"""
Потребитель событий RabbitMQ для Inventory Service
Подписывается на события от других сервисов и создает операции
"""
import pika
import json
import logging
import asyncio
from typing import Dict, Any
from app.config import settings
from app.database import SessionLocal
from app.inventory_service import InventoryService
from app.catalog_client import catalog_client

logger = logging.getLogger(__name__)


class EventConsumer:
    """Потребитель событий RabbitMQ"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self._running = False
    
    def _connect(self):
        """Установить соединение с RabbitMQ"""
        max_retries = 5
        retry_delay = 5  # секунд
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to RabbitMQ (attempt {attempt + 1}/{max_retries})...")
                logger.info(f"RabbitMQ host: {settings.RABBITMQ_HOST}, port: {settings.RABBITMQ_PORT}")
                
                credentials = pika.PlainCredentials(
                    settings.RABBITMQ_USER,
                    settings.RABBITMQ_PASSWORD
                )
                parameters = pika.ConnectionParameters(
                    host=settings.RABBITMQ_HOST,
                    port=settings.RABBITMQ_PORT,
                    credentials=credentials,
                    connection_attempts=3,
                    retry_delay=2
                )
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                # Объявить exchange
                self.channel.exchange_declare(
                    exchange='erp_events',
                    exchange_type='topic',
                    durable=True
                )
                
                # Создать очередь для Inventory Service
                queue_result = self.channel.queue_declare(
                    queue='inventory_service_queue',
                    durable=True
                )
                queue_name = queue_result.method.queue
                
                # Подписаться на события от Catalog Service
                self.channel.queue_bind(
                    exchange='erp_events',
                    queue=queue_name,
                    routing_key='sku.created'
                )
                self.channel.queue_bind(
                    exchange='erp_events',
                    queue=queue_name,
                    routing_key='sku.updated'
                )
                self.channel.queue_bind(
                    exchange='erp_events',
                    queue=queue_name,
                    routing_key='sku.deleted'
                )
                
                # Настроить обработчик сообщений
                self.channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=self._handle_message,
                    auto_ack=False
                )
                
                logger.info("Successfully connected to RabbitMQ and subscribed to events")
                return True
            except Exception as e:
                import traceback
                error_msg = str(e)
                error_trace = traceback.format_exc()
                logger.error(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}): {error_msg}")
                logger.debug(f"Full traceback: {error_trace}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    import time
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached. Failed to connect to RabbitMQ.")
                    logger.error(f"Final error: {error_msg}")
                    logger.error(f"Final traceback: {error_trace}")
                    return False
        return False
    
    def _handle_message(self, ch, method, properties, body):
        """Обработать сообщение из RabbitMQ"""
        try:
            message = json.loads(body)
            routing_key = method.routing_key
            
            logger.info(f"Received event: {routing_key}, data: {message}")
            
            # Обрабатываем событие в зависимости от типа
            if routing_key == 'sku.created':
                self._handle_sku_created(message)
            elif routing_key == 'sku.updated':
                self._handle_sku_updated(message)
            elif routing_key == 'sku.deleted':
                self._handle_sku_deleted(message)
            
            # Подтверждаем обработку сообщения
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            # Отклоняем сообщение при ошибке
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def _handle_sku_created(self, data: Dict[str, Any]):
        """Обработать событие создания товара"""
        try:
            sku_id = data.get('sku_id')
            if not sku_id:
                logger.error("sku_id not found in event data")
                return
            
            # Получаем полную информацию о товаре из Catalog Service
            # Используем синхронный вызов, так как мы в callback
            import httpx
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{settings.CATALOG_SERVICE_URL}/catalog/skus/{sku_id}")
                if response.status_code != 200:
                    logger.error(f"Failed to fetch SKU {sku_id} from Catalog Service")
                    return
                
                sku_data = response.json()
            
            # Получаем информацию о единицах измерения
            weight_unit_name = sku_data.get('weight_unit', {}).get('name', 'кг')
            quantity_unit_name = sku_data.get('quantity_unit', {}).get('name', 'шт')
            
            # Создаем операцию в Inventory Service
            db = SessionLocal()
            try:
                # Для создания товара используем локацию "хранилище" (по умолчанию)
                # Количество и вес берем из товара
                quantity_value = int(float(sku_data.get('quantity', '1')))
                weight_value = float(sku_data.get('weight', '1'))
                
                # Рассчитываем delta_value используя InventoryService
                delta_value = await InventoryService.calculate_delta_value(
                    quantity_value,
                    quantity_unit_name,
                    weight_value,
                    weight_unit_name
                )
                
                # Создаем операцию и обновляем остатки
                await InventoryService.create_operation(
                    db,
                    operation_type='create',
                    sku_id=sku_id,
                    quantity_value=quantity_value,
                    quantity_unit=quantity_unit_name,
                    weight_value=int(weight_value),
                    weight_unit=weight_unit_name,
                    source_location='хранилище'
                )
                logger.info(f"Created inventory operation for SKU {sku_id}")
            except Exception as e:
                logger.error(f"Error creating inventory operation for SKU {sku_id}: {e}")
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error handling sku.created event: {e}")
    
    def _handle_sku_updated(self, data: Dict[str, Any]):
        """Обработать событие обновления товара"""
        try:
            sku_id = data.get('sku_id')
            if not sku_id:
                logger.error("sku_id not found in event data")
                return
            
            # Получаем полную информацию о товаре из Catalog Service
            import httpx
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{settings.CATALOG_SERVICE_URL}/catalog/skus/{sku_id}")
                if response.status_code != 200:
                    logger.error(f"Failed to fetch SKU {sku_id} from Catalog Service")
                    return
                
                sku_data = response.json()
            
            # Получаем информацию о единицах измерения
            weight_unit_name = sku_data.get('weight_unit', {}).get('name', 'кг')
            quantity_unit_name = sku_data.get('quantity_unit', {}).get('name', 'шт')
            
            # Создаем операцию в Inventory Service
            db = SessionLocal()
            try:
                quantity_value = int(float(sku_data.get('quantity', '1')))
                weight_value = float(sku_data.get('weight', '1'))
                
                # Получаем старые значения из существующей записи остатков (если есть)
                from app.models import InventorySKUTotal
                old_sku_total = db.query(InventorySKUTotal).filter(InventorySKUTotal.sku_id == sku_id).first()
                
                if old_sku_total:
                    # Если запись существует, нужно обновить остатки
                    # Рассчитываем новое delta_value
                    new_delta_value = await InventoryService.calculate_delta_value(
                        quantity_value,
                        quantity_unit_name,
                        weight_value,
                        weight_unit_name
                    )
                    
                    # Обновляем остатки: вычитаем старое значение и добавляем новое
                    old_delta_value = old_sku_total.total_weight
                    delta_diff = new_delta_value - old_delta_value
                    
                    # Обновляем запись остатков
                    old_sku_total.total_weight = new_delta_value
                    old_sku_total.sku_name = sku_data.get('name', 'Unknown')
                    
                    # Обновляем остатки по локациям
                    from app.models import InventoryLocationTotal
                    location_totals = db.query(InventoryLocationTotal).filter(
                        InventoryLocationTotal.sku_id == sku_id
                    ).all()
                    
                    for location_total in location_totals:
                        # Пересчитываем вес для каждой локации пропорционально
                        if old_delta_value > 0:
                            ratio = location_total.weight / old_delta_value
                            location_total.weight = int(new_delta_value * ratio)
                        else:
                            location_total.weight = new_delta_value
                        location_total.sku_name = sku_data.get('name', 'Unknown')
                    
                    # Создаем операцию
                    from app.models import InventoryOperation
                    operation = InventoryOperation(
                        operation_type='update',
                        sku_id=sku_id,
                        sku_name=sku_data.get('name', 'Unknown'),
                        quantity_value=quantity_value,
                        quantity_unit=quantity_unit_name,
                        weight_value=int(weight_value),
                        weight_unit=weight_unit_name,
                        delta_value=new_delta_value,
                        delta_unit='кг',
                        source_location='хранилище',
                        target_location='хранилище'
                    )
                    db.add(operation)
                    db.commit()
                    logger.info(f"Updated inventory totals and created operation for SKU {sku_id}")
                else:
                    # Если записи нет, создаем новую (как при create)
                    await InventoryService.create_operation(
                        db,
                        operation_type='create',
                        sku_id=sku_id,
                        quantity_value=quantity_value,
                        quantity_unit=quantity_unit_name,
                        weight_value=int(weight_value),
                        weight_unit=weight_unit_name,
                        source_location='хранилище'
                    )
                    logger.info(f"Created inventory operation for updated SKU {sku_id} (new record)")
            except Exception as e:
                logger.error(f"Error creating inventory operation for updated SKU {sku_id}: {e}")
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error handling sku.updated event: {e}")
    
    def _handle_sku_deleted(self, data: Dict[str, Any]):
        """Обработать событие удаления товара"""
        try:
            sku_id = data.get('sku_id')
            if not sku_id:
                logger.error("sku_id not found in event data")
                return
            
            # Получаем данные из остатков перед удалением
            db = SessionLocal()
            try:
                from app.models import InventoryOperation, InventorySKUTotal
                
                # Получаем данные из остатков
                sku_total = db.query(InventorySKUTotal).filter(InventorySKUTotal.sku_id == sku_id).first()
                
                if sku_total:
                    # Используем данные из остатков
                    quantity_value = sku_total.total_quantity if sku_total.total_quantity > 0 else 1
                    weight_value = sku_total.total_weight
                    sku_name = sku_total.sku_name
                    delta_value = -sku_total.total_weight  # Отрицательное значение при удалении
                else:
                    # Если остатков нет, используем данные из события
                    quantity_value = 0
                    weight_value = 0
                    sku_name = data.get('name', 'Unknown')
                    delta_value = 0
                
                # Создаем операцию
                operation = InventoryOperation(
                    operation_type='delete',
                    sku_id=sku_id,
                    sku_name=sku_name,
                    quantity_value=quantity_value,
                    quantity_unit='шт',
                    weight_value=weight_value,
                    weight_unit='кг',
                    delta_value=delta_value,
                    delta_unit='кг',
                    source_location='хранилище',
                    target_location='хранилище'
                )
                db.add(operation)
                
                # Обновляем остатки (уменьшаем до нуля)
                if sku_total:
                    sku_total.total_weight = 0
                    sku_total.total_quantity = 0
                
                db.commit()
                logger.info(f"Created inventory operation for deleted SKU {sku_id}")
            except Exception as e:
                logger.error(f"Error creating inventory operation for deleted SKU {sku_id}: {e}")
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error handling sku.deleted event: {e}")
    
    def start(self):
        """Запустить потребитель"""
        logger.info("Starting RabbitMQ event consumer...")
        if self._connect():
            self._running = True
            logger.info("RabbitMQ event consumer is running and waiting for messages...")
            try:
                self.channel.start_consuming()
            except KeyboardInterrupt:
                logger.info("Stopping RabbitMQ event consumer...")
                self.stop()
            except Exception as e:
                logger.error(f"Error in RabbitMQ consumer: {e}")
                self._running = False
        else:
            logger.error("Failed to start RabbitMQ event consumer - will retry on next message")
            self._running = False
    
    def stop(self):
        """Остановить потребитель"""
        self._running = False
        if self.channel and not self.channel.is_closed:
            self.channel.stop_consuming()
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        logger.info("RabbitMQ event consumer stopped")


# Глобальный экземпляр потребителя
event_consumer = EventConsumer()

