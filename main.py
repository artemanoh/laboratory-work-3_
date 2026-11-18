import io
import logging
import sys
import unittest
from contextlib import redirect_stdout

from models import Device, IPhone, MacBook, Master, ServiceOrder, SparePart
from service import AppleService

def main():
logging.basicConfig(
level=logging.INFO,
format="%(asctime)s | %(levelname)s | %(message)s",
datefmt="%H:%M:%S",
stream=sys.stdout,
)

hub = AppleService("iStore Official Lab")

# Запчастини
hub.add_part(SparePart("Заміна батареї iPhone", stock_quantity=2, price=2800.0))
hub.add_part(SparePart("Чистка та заміна клавіатури Mac", stock_quantity=1, price=3400.0))
hub.add_part(SparePart("Заміна камери iPhone", stock_quantity=0, price=3100.0))

# Майстри
hub.add_master(Master("Олексій", max_load=2))
hub.add_master(Master("Артем", max_load=1))

# Пристрої
phone1 = IPhone(
    model="iPhone 15 Pro",
    serial_number="SN-40291",
    issue="Заміна батареї iPhone",
    battery_health=74,
    face_id_ok=True,
)
laptop = MacBook(
    model="MacBook Air M2",
    serial_number="SN-55210",
    issue="Чистка та заміна клавіатури Mac",
    screen_size=13.6,
    cpu_temp=86.4,
    ssd_life_percent=95,
)
phone2 = IPhone(
    model="iPhone 13 Pro",
    serial_number="SN-10294",
    issue="Заміна камери iPhone",
    battery_health=89,
    face_id_ok=False,
)

hub.add_order(ServiceOrder(101, "Артем", phone1))
hub.add_order(ServiceOrder(102, "Вікторія", laptop))
hub.add_order(ServiceOrder(103, "Максим", phone2))

hub.process_all_orders()
hub.show_report()
class ServiceTests(unittest.TestCase):
def setUp(self):
# Перед кожним тестом створюємо новий сервіс із чистим складом і балансом.
self.hub = AppleService("Тестовий сервіс")
self.part = SparePart("Заміна батареї iPhone", 2, 2800.0)
self.master = Master("Олексій", max_load=1)
self.phone = IPhone("iPhone 15 Pro", "TEST-1", self.part.part_name)
self.order = ServiceOrder(101, "Артем", self.phone)

    self.hub.add_part(self.part)
    self.hub.add_master(self.master)
    self.hub.add_order(self.order)

def test_device_requires_diagnostics(self):
    """Базовий пристрій без реалізації діагностики створити неможливо."""
    with self.assertRaises(TypeError):
        Device("Пристрій", "TEST", "Несправність")

def test_device_diagnostics(self):
    """iPhone і MacBook виконують різні перевірки."""
    phone = IPhone("iPhone", "TEST-2", "Камера", battery_health=74, face_id_ok=False)
    laptop = MacBook("MacBook", "TEST-3", "Клавіатура", cpu_temp=86.4)

    phone_output = io.StringIO()
    with redirect_stdout(phone_output):
        phone.run_diagnostics()

    laptop_output = io.StringIO()
    with redirect_stdout(laptop_output):
        laptop.run_diagnostics()

    self.assertIn("нижче 80%", phone_output.getvalue())
    self.assertIn("Апаратний збій", phone_output.getvalue())
    self.assertIn("критичний перегрів", laptop_output.getvalue())

def test_successful_repair_counted_once(self):
    """Повторна обробка не списує другу деталь і не подвоює виручку."""
    with redirect_stdout(io.StringIO()), self.assertLogs("service", level="INFO") as log:
        self.hub.process_all_orders()
        self.hub.process_all_orders()

    self.assertTrue(self.phone.is_fixed)
    self.assertTrue(self.master.can_take_task())
    self.assertEqual(self.part.stock_quantity, 1)
    self.assertEqual(self.order.cost, 3400.0)
    self.assertEqual(self.hub.revenue, 3400.0)
    self.assertEqual(len(log.records), 1)
    self.assertIn("#101", log.records[0].getMessage())

def test_missing_part(self):
    """Якщо деталь закінчилася, ремонт очікує, а виручка залишається нульовою."""
    self.part.take_one()
    self.part.take_one()

    with redirect_stdout(io.StringIO()), self.assertLogs("service", level="WARNING") as log:
        self.hub.process_all_orders()

    self.assertFalse(self.phone.is_fixed)
    self.assertEqual(self.hub.revenue, 0.0)
    self.assertIn("Немає деталі", log.records[0].getMessage())

def test_busy_master(self):
    """Якщо майстер зайнятий, деталь залишається на складі до його звільнення."""
    self.master.assign_task()

    with redirect_stdout(io.StringIO()), self.
assertLogs("service", level="WARNING") as log:
        self.hub.process_all_orders()

    self.assertFalse(self.phone.is_fixed)
    self.assertEqual(self.part.stock_quantity, 2)
    self.assertIn("Усі майстри зайняті", log.records[0].getMessage())

    self.master.complete_task()
    with redirect_stdout(io.StringIO()):
        self.hub.process_all_orders()

    self.assertTrue(self.phone.is_fixed)
    self.assertEqual(self.part.stock_quantity, 1)
if name == "main":
main()
