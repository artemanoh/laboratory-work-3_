import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from models import Device, IPhone, MacBook, Master, ServiceOrder, SparePart
from service import AppleService
from storage import JsonStorage, Storage


class FakeStorage(Storage):
    def read(self): return {}
    def write(self, data): self.saved = data


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.storage = FakeStorage()
        self.hub = AppleService("Тест", self.storage)
        self.part = SparePart("Батарея", 2, 2800)
        self.master = Master("Олексій", 1)
        self.phone = IPhone("iPhone", "SN", "Батарея")
        self.hub.add_part(self.part)
        self.hub.add_master(self.master)
        self.hub.add_order(ServiceOrder(101, "Артем", self.phone))

    def test_interface(self):
        with self.assertRaises(TypeError):
            Device("Пристрій", "SN", "Батарея")

    def test_diagnostics(self):
        with redirect_stdout(io.StringIO()) as result:
            IPhone("iPhone", "SN", "Батарея", battery_health=70).run_diagnostics()
        self.assertIn("нижче 80%", result.getvalue())
        with redirect_stdout(io.StringIO()) as result:
            MacBook("MacBook", "SN", "Клавіатура", cpu_temp=90).run_diagnostics()
        self.assertIn("критичний перегрів", result.getvalue())

    def test_repair_once(self):
        with redirect_stdout(io.StringIO()):
            self.hub.process_all_orders()
            self.hub.process_all_orders()
        self.assertEqual(self.hub.revenue, 3400)
        self.assertEqual(self.part.stock_quantity, 1)
        self.assertTrue(self.phone.is_fixed)

    def test_no_part(self):
        self.part.take_one(); self.part.take_one()
        with redirect_stdout(io.StringIO()), self.assertLogs("service", "WARNING"):
            self.hub.process_all_orders()
        self.assertFalse(self.phone.is_fixed)

    def test_busy_master(self):
        self.master.assign_task()
        with redirect_stdout(io.StringIO()), self.assertLogs("service", "WARNING"):
            self.hub.process_all_orders()
        self.assertEqual(self.part.stock_quantity, 2)
        self.master.complete_task()

    def test_dependency_injection(self):
        with redirect_stdout(io.StringIO()):
            self.hub.process_all_orders()
        self.hub.save_report()
        self.assertEqual(self.storage.saved["revenue"], 3400)

    def test_json_files(self):
        with tempfile.TemporaryDirectory() as folder:
            src, dst = Path(folder) / "input.json", Path(folder) / "output.json"
            src.write_text('{"orders": []}', encoding="utf-8")
            store = JsonStorage(src, dst)
            self.assertEqual(store.read(), {"orders": []})
            store.write({"message": "Успіх"})
            self.assertEqual(json.loads(dst.read_text(encoding="utf-8"))["message"], "Успіх")

    def test_bad_json(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / "bad.json"
            src.write_text("{не JSON", encoding="utf-8")
            with self.assertRaises(ValueError):
                JsonStorage(src, Path(folder) / "output.json").read()


if __name__ == "__main__":
    unittest.main()