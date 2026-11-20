import logging
from contextlib import redirect_stdout
from pathlib import Path

from models import IPhone, MacBook, Master, ServiceOrder, SparePart
from service import AppleService
from storage import JsonStorage

BASE = Path(__file__).resolve().parent


def main():
    (BASE / "logs").mkdir(exist_ok=True)
    logging.basicConfig(
        filename=BASE / "logs" / "service.log", encoding="utf-8",
        level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
    )
    # Передаємо готове сховище в сервіс — це Dependency Injection.
    storage = JsonStorage(BASE / "data/input.json", BASE / "data/output.json")
    hub = AppleService("iStore Official Lab", storage)

    try:
        data = storage.read()
        hub.title = data.get("service_title", hub.title)
        for part in data["parts"]:
            hub.add_part(SparePart(**part))
        for master in data["masters"]:
            hub.add_master(Master(**master))

        types = {"iphone": IPhone, "macbook": MacBook}
        for item in data["orders"]:
            details = item["device"].copy()
            kind = details.pop("type").lower()
            if kind not in types:
                raise ValueError(f"Невідомий тип пристрою: {kind}")
            device = types[kind](**details)
            hub.add_order(ServiceOrder(item["order_id"], item["client_name"], device))

        # Діагностику та квитанції записуємо у файл, а не в консоль.
        with (BASE / "data/report.txt").open("w", encoding="utf-8") as file:
            with redirect_stdout(file):
                hub.process_all_orders()
                hub.show_report()
        hub.save_report()
    except (OSError, ValueError, KeyError, TypeError) as error:
        logging.exception("Помилка роботи програми")
        print(f"Помилка: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())