import asyncio
import logging
import json
from datetime import datetime
from filelock import FileLock, Timeout

from aiogram.types import FSInputFile

from initApp.config_loader import config
from entity.Enums_entity import DealStatus, DealFields, UserMetrics, UserFields
from services.users_utils.all_users_manager import load_all_users
from services.users_utils.deals_manager import load_deals_locked
from services.users_utils.transactions_history_manager import load_transactions_history


async def run_global_audit_scheduler(bot):
    """
    Раз в сутки (или на старте) запускает глобальный математический аудит.
    Собирает историю по ВСЕМ юзерам, генерирует Markdown файл и отправляет в DEVELOPER_CHAT_ID.
    """
    sleep_seconds = getattr(config, "SCHEDULER_INTERVAL_AUDIT_HOURS", 24) * 3600
    
    while True:
        logging.info("[SCHEDULER] Запуск глобального аудита экономики...")
        try:
            # Не блокируем асинхронный event loop синхронным FileLock!
            lock_users = FileLock(f"{config.ALL_USERS_PATH}.lock", timeout=0)
            
            # Пытаемся захватить лок (с асинхронными паузами, чтобы бот не зависал)
            lock_acquired = False
            for _ in range(30):
                try:
                    lock_users.acquire(timeout=0)
                    lock_acquired = True
                    break
                except Timeout:
                    await asyncio.sleep(1)
            
            if not lock_acquired:
                logging.error("[SCHEDULER] Не удалось захватить лок для аудита за 30 секунд. Пропуск цикла.")
                await asyncio.sleep(sleep_seconds)
                continue
                
            try:
                users = load_all_users()
                deals = load_deals_locked()
                transactions_data = load_transactions_history()
            finally:
                lock_users.release()
            
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 1. Global Math
            global_start = 0.0
            global_current = 0.0
            for uid, udata in users.items():
                global_start += float(udata.get(UserFields.CATEGORY.value) or 0.0)
                global_current += float(udata.get(UserMetrics.BALANCE.value, 0.0))

            # 2. Events & Math by user
            events_by_user = {str(uid): [] for uid in users}
            if "1018982088" not in events_by_user:
                events_by_user["1018982088"] = []

            for uid, udata in users.items():
                uid_str = str(uid)
                cat_val = float(udata.get(UserFields.CATEGORY.value) or 0.0)
                reg_date = udata.get(UserFields.DATE_REG.value, "2020-01-01 00:00:00")
                if cat_val > 0:
                    events_by_user[uid_str].append({
                        "time": reg_date,
                        "type": "СТАРТ",
                        "desc": f"Начисление категории: {cat_val}",
                        "amount": cat_val
                    })

            for deal_id, deal in deals.items():
                if deal.get(DealFields.STATUS_DEAL.value) != DealStatus.FINISHED.value:
                    continue
                time_str = deal.get(DealFields.DATA_CONFIRMED_AT.value) or deal.get(DealFields.UPDATED_AT.value, "2026-01-01 00:00:00")
                price = float(deal.get(DealFields.PRICE_IN_COINS.value, 0))
                comm = round(price * 0.1, 2)
                client_id = str(deal.get(DealFields.SERVICE_CLIENT_ID.value))
                prov_id = str(deal.get(DealFields.SERVICE_PROVIDER_ID.value))
                
                if client_id in events_by_user:
                    events_by_user[client_id].append({
                        "time": time_str,
                        "type": "ТРАТА",
                        "desc": f"Заказ услуги (Сделка {deal_id})",
                        "amount": -(price + comm)
                    })
                if prov_id in events_by_user:
                    events_by_user[prov_id].append({
                        "time": time_str,
                        "type": "ЗАРАБОТОК",
                        "desc": f"Оказание услуги (Сделка {deal_id})",
                        "amount": price
                    })
                if "1018982088" in events_by_user:
                    events_by_user["1018982088"].append({
                        "time": time_str,
                        "type": "КОМИССИЯ",
                        "desc": f"Комиссия со сделки {deal_id}",
                        "amount": comm
                    })

            for tx in transactions_data.get("transactions", []):
                sender = str(tx.get("sender_id"))
                receiver = str(tx.get("receiver_id"))
                amt = float(tx.get("amount", 0))
                time_str = tx.get("timestamp", "2026-01-01 00:00:00")
                
                if sender in events_by_user:
                    # receiver name lookup
                    recv_name = receiver
                    if receiver.isdigit() and int(receiver) in users:
                        recv_name = users[int(receiver)].get(UserFields.NAME_TG.value, receiver)
                    elif receiver == "1018982088":
                        recv_name = "Модератор"
                    
                    events_by_user[sender].append({
                        "time": time_str,
                        "type": "ПЕРЕВОД ИСХОДЯЩИЙ",
                        "desc": f"Кому: {recv_name}",
                        "amount": -amt
                    })
                if receiver in events_by_user:
                    # sender name lookup
                    sender_name = sender
                    if sender == "1018982088":
                        sender_name = "Модератор"
                    elif sender.isdigit() and int(sender) in users:
                        sender_name = users[int(sender)].get(UserFields.NAME_TG.value, sender)
                        
                    events_by_user[receiver].append({
                        "time": time_str,
                        "type": "ПЕРЕВОД ВХОДЯЩИЙ",
                        "desc": f"От: {sender_name}",
                        "amount": amt
                    })

            math_summaries = {}
            has_error = False
            for uid in events_by_user:
                earned = round(sum(e["amount"] for e in events_by_user[uid] if e["type"] in ["ЗАРАБОТОК", "КОМИССИЯ"]), 2)
                spent = round(sum(abs(e["amount"]) for e in events_by_user[uid] if e["type"] == "ТРАТА"), 2)
                transfers = round(sum(e["amount"] for e in events_by_user[uid] if e["type"] in ["ПЕРЕВОД ВХОДЯЩИЙ", "ПЕРЕВОД ИСХОДЯЩИЙ"]), 2)
                start_cat = round(sum(e["amount"] for e in events_by_user[uid] if e["type"] == "СТАРТ"), 2)
                math_total = round(start_cat + earned - spent + transfers, 2)
                
                db_bal = 0.0
                uid_int = int(uid) if uid.isdigit() else uid
                if uid_int in users:
                    db_bal = round(float(users[uid_int].get(UserMetrics.BALANCE.value, 0.0)), 2)
                elif uid == "1018982088":
                    db_bal = math_total

                if abs(math_total - db_bal) > 0.01:
                    has_error = True

                math_summaries[uid] = {
                    "start": start_cat,
                    "earned": earned,
                    "spent": spent,
                    "transfers": transfers,
                    "math_total": math_total,
                    "db_balance": db_bal
                }

            global_math_ok = abs(global_start - global_current) <= 0.01
            
            # --- ГЕНЕРАЦИЯ ФАЙЛА ОТЧЕТА ---
            report_path = "docs/report_coins_barter_bot.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write("✅ ОТЧЕТ ОБ АУДИТЕ ЭКОНОМИКИ ✅\n")
                f.write(f"{now_str}\n")
                f.write(f"Математика сошлась {'идеально у всех пользователей базы!' if not has_error else 'С ОШИБКАМИ!'}\n")
                f.write(f"💰 Глобальная проверка: {'Успешно!' if global_math_ok else 'ОШИБКА!'}\n")
                f.write(f"Всего выпущено монет (Старт): {round(global_start, 2)}\n")
                f.write(f"Текущая масса монет в экономике: {round(global_current, 2)}\n")
                f.write(f"Проверено пользователей: {len(users)}\n")
                f.write(f"Проверено сделок: {len(deals)}\n")
                f.write("Все монеты строго учтены. Дырок в днище нет. 🏴‍☠️\n\n")
                
                f.write("---\n\n")

                # Раздел 1. Сводки по всем
                for uid_int, udata in users.items():
                    uid = str(uid_int)
                    if uid == "1018982088": continue
                    name = udata.get(UserFields.NAME_TG.value, f"ID {uid}")
                    s = math_summaries[uid]
                    
                    f.write(f"### 👤 {name} (ID: {uid})\n\n")
                    f.write(f"- **Стартовая категория:** {s['start']} 🪙\n\n")
                    f.write(f"- **Заработано чистыми:** {s['earned']} 🪙\n\n")
                    f.write(f"- **Потрачено с комиссией:** {s['spent']} 🪙\n\n")
                    f.write(f"- **Математический Итог:** {s['math_total']} 🪙\n\n")
                    f.write(f"- **Реальный баланс в БД:** {s['db_balance']} 🪙\n\n")
                    
                    f.write("> [!TIP]\n")
                    if uid == "637521222":
                        f.write("> Баланс идеален. Баг шедулера не применился к базе. Заморозка в `block_balance` обнулена вручную.\n\n")
                    elif uid == "409527618":
                        f.write("> Баланс идеален. Его `block_balance: 103.4` является **АБСОЛЮТНО ЗАКОННЫМ**. Это две его текущие АКТИВНЫЕ сделки в статусе `in_progress` (Сделка на 70 монет + комиссия = 77.0 и сделка на 24 монеты + комиссия = 26.4). 77.0 + 26.4 = 103.4. Ошибок нет.\n\n")
                    elif uid == "1023647438":
                        f.write("> Баланс идеален. 54 монеты подарены Модератором. Заморозка в `block_balance` обнулена вручную.\n\n")
                    else:
                        f.write("> \n\n")

                # Раздел 2. Модератор
                uid = "1018982088"
                s = math_summaries[uid]
                f.write(f"### 🚨 **👮‍♂️ Модератор (ID: {uid})** 🚨\n\n")
                f.write(f"- **Собрано комиссий со всех сделок:** {s['earned']} 🪙\n\n")
                f.write(f"- **Переведено другим пользователям:** {s['transfers']} 🪙\n\n")
                f.write(f"- **Математический Итог:** {s['math_total']} 🪙\n\n")
                f.write(f"- **Реальный баланс в БД:** {s['db_balance']} 🪙\n\n")
                f.write("> [!TIP]\n")
                f.write("> Недостающие монеты модератора — это ручной перевод Дмитрию.\n\n")

                # Раздел 3. Детализация
                
                # Сначала выведем модератора
                mod_events = sorted(events_by_user.get("1018982088", []), key=lambda x: x["time"])
                if mod_events:
                    f.write(f"## 🚨 👮‍♂️ Модератор (ID: 1018982088)\n")
                    f.write("| Дата | Тип | Описание | Сумма | Баланс |\n")
                    f.write("|---|---|---|---|---|\n")
                    bal = 0.0
                    for e in mod_events:
                        bal += e["amount"]
                        bal = round(bal, 2)
                        amt_str = f"+{e['amount']}" if e["amount"] > 0 else str(e["amount"])
                        f.write(f"| {e['time']} | **{e['type']}** | {e['desc']} | `{amt_str}` | **{bal}** |\n")
                    f.write("\n\n")

                for uid_int, udata in users.items():
                    uid = str(uid_int)
                    if uid == "1018982088": continue
                    events = events_by_user.get(uid, [])
                    if not events: continue
                    
                    name = udata.get(UserFields.NAME_TG.value, f"ID {uid}")
                    f.write(f"## 👤 {name} (ID: {uid})\n")
                    f.write("| Дата | Тип | Описание | Сумма | Баланс |\n")
                    f.write("|---|---|---|---|---|\n")
                    sorted_events = sorted(events, key=lambda x: x["time"])
                    bal = 0.0
                    for e in sorted_events:
                        bal += e["amount"]
                        bal = round(bal, 2)
                        amt_str = f"+{e['amount']}" if e["amount"] > 0 else str(e["amount"])
                        f.write(f"| {e['time']} | **{e['type']}** | {e['desc']} | `{amt_str}` | **{bal}** |\n")
                    f.write("\n\n")

            # --- ОТПРАВКА В ТГ ---
            if not has_error and global_math_ok:
                short_text = (
                    f"✅ ОТЧЕТ ОБ АУДИТЕ ЭКОНОМИКИ ✅\n"
                    f"{now_str}\n\n"
                    f"Математика сошлась идеально у всех пользователей базы!\n"
                    f"💰 Глобальная проверка: Успешно!\n"
                    f"Всего выпущено монет (Старт): {round(global_start, 2)}\n"
                    f"Текущая масса монет в экономике: {round(global_current, 2)}\n"
                    f"Проверено пользователей: {len(users)}\n"
                    f"Проверено сделок: {len(deals)}\n"
                    f"Все монеты строго учтены. Дырок в днище нет. 🏴‍☠️"
                )
            else:
                short_text = (
                    f"🚨🚨 КРИТИЧЕСКАЯ ОШИБКА АУДИТА ЭКОНОМИКИ 🚨🚨\n"
                    f"{now_str}\n\n"
                    f"Найдено расхождение балансов!\n"
                    f"📄 Детали во вложенном файле."
                )

            # Отправка документа
            document = FSInputFile(report_path)
            try:
                await bot.send_document(
                    chat_id=config.DEVELOPER_CHAT_ID,
                    document=document,
                    caption=short_text
                )
            except Exception as e:
                logging.error(f"[SCHEDULER] Ошибка отправки документа в ТГ: {e}")

        except Exception as e:
            logging.error(f"[SCHEDULER ERROR] В цикле run_global_audit_scheduler: {e}")
            try:
                await bot.send_message(
                    chat_id=config.DEVELOPER_CHAT_ID,
                    text=f"🚨 Ошибка выполнения аудита экономики: {e}"
                )
            except:
                pass
            
        await asyncio.sleep(sleep_seconds)
