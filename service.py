import logging
from models import Master, Reportable, ServiceOrder, SparePart
from storage import Storage

logger = logging.getLogger(__name__)


class AppleService(Reportable):
    """Диспетчерська система сервісного центру."""

    def __init__(self, title: str, storage: Storage):
        self.title = title
        self.storage = storage  # Dependency Injection
        self.parts = []
        self.masters = []
        self.orders = []
        self.__revenue = 0.0

    @property
    def revenue(self) -> float:
        return self.__revenue

    def add_part(self, part: SparePart):
        self.parts.append(part)

    def add_master(self, master: Master):
        self.masters.append(master)

    def add_order(self, order: ServiceOrder):
        self.orders.append(order)
        logger.info("Прийнято замовлення #%s від %s", order.order_id, order.client_name)

    def process_all_orders(self):
        print("\n" + "=" * 50)
        print(f"ЗАПУСК АВТОМАТИЧНОЇ ОБРОБКИ ЗАМОВЛЕНЬ У {self.title}")
        print("=" * 50)

        for order in self.orders:
            dev = order.device
            if dev.is_fixed:
                continue
            print(f"\n>>> ОБРОБКА ЗАМОВЛЕННЯ #{order.order_id} (клієнт: {order.client_name})")
            diagnostic_summary = dev.run_diagnostics()
            print(f"  Підсумок перевірки: {diagnostic_summary}")

            needed_part = None
            for part in self.parts:
                if part.part_name == dev.issue:
                    needed_part = part
                    break
            if needed_part is None or needed_part.stock_quantity == 0:
                logger.warning("#%s: Немає деталі '%s' на складі", order.order_id, dev.issue)
                continue

            available_master = None
            for master in self.masters:
                if master.can_take_task():
                    available_master = master
                    break
            if available_master is None:
                logger.warning("#%s: Усі майстри зайняті. Замовлення очікує", order.order_id)
                continue

            available_master.assign_task()
            try:
                needed_part.take_one()
                dev.mark_as_fixed()
                order.set_cost(needed_part.price)
                self.__revenue += order.cost
                logger.info("#%s: Майстер %s виконав ремонт. Чек: %.2f грн",
                            order.order_id, available_master.name, order.cost)
            finally:
                available_master.complete_task()

    def show_report(self) -> None:
        print("\n" + "=" * 50)
        print(f"ПІДСУМКОВИЙ ЗВІТ: {self.title}")
        print("=" * 50)
        print("Залишки деталей на складі:")
        for part in self.parts:
            print(" - " + part.get_info())
        print("\nОформлені квитанції:")
        for order in self.orders:
            if order.device.is_fixed:
                order.print_receipt()
        print(f"\nЗагальна виручка сервісу: {self.revenue:.2f} грн")

    def save_report(self):
        self.storage.write({
            "service": self.title,
            "revenue": self.revenue,
            "orders": [
                {"id": o.order_id, "client": o.client_name, "device": o.device.model,
                 "status": "Відремонтовано" if o.device.is_fixed else "Очікує",
                 "cost": o.cost}
                for o in self.orders
            ],
            "parts": [{"name": p.part_name, "stock": p.stock_quantity} for p in self.parts]
        })
        logger.info("Звіт збережено у JSON-файл")