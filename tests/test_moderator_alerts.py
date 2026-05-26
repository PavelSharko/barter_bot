# tests/test_moderator_alerts.py
import unittest
import asyncio
import logging
import sys
import os
import shutil
import warnings

# Добавляем корень проекта в пути импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Принудительно устанавливаем стенд "test" для запуска тестов
os.environ["STEND"] = "test"

# Глушим докучливые предупреждения о закрытии SSL сокетов Google Drive/Aiogram
warnings.filterwarnings(action="ignore", category=ResourceWarning)

from initApp.config_loader import config
from repository.google_drive_manager import download_db_folder
from services.users_utils.all_users_manager import load_all_users
from services.users_utils.user_profile_manager import load_profiles
from services.msgs_utils.alert_formatter import (
    format_new_deal_alert,
    format_deal_completed_alert,
    format_deal_blocked_alert,
    format_profile_changed_alert,
    format_new_registration_alert,
    format_deal_auto_cancelled_alert
)
from aiogram import Bot

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

class TestModeratorAlerts(unittest.IsolatedAsyncioTestCase):
    _db_downloaded_by_us = False

    @classmethod
    def setUpClass(cls):
        """Скачивает базу ОДИН РАЗ перед запуском всего сьюта тестов, если её еще нет."""
        super().setUpClass()
        if not os.path.exists(config.DB_STORGE):
            logging.info("⬇️ Скачивание тестовой базы данных из Google Drive согласно конфигу...")
            asyncio.run(download_db_folder())
            cls._db_downloaded_by_us = True
        else:
            logging.info("📁 Тестовая база данных уже присутствует локально. Пропускаем скачивание.")

    @classmethod
    def tearDownClass(cls):
        """Удаляет скачанную тестовую папку, если она была скачана именно этим тестом."""
        if cls._db_downloaded_by_us and os.path.exists(config.DB_STORGE):
            logging.info("🧹 Очистка временной тестовой базы данных...")
            try:
                shutil.rmtree(config.DB_STORGE)
                logging.info("🗑 Временная папка успешно удалена.")
            except Exception as e:
                logging.error(f"Не удалось удалить временную папку {config.DB_STORGE}: {e}")
        super().tearDownClass()

    async def asyncSetUp(self):
        """Инициализация перед каждым отдельным тестом: загрузка данных без повторного скачивания"""
        self.users = load_all_users()
        self.profiles = load_profiles()
        
        # Динамически выбираем двух любых пользователей из базы для тестов (никакого хардкода!)
        user_ids = list(self.users.keys())
        if len(user_ids) < 2:
            raise unittest.SkipTest("Недостаточно пользователей в тестовой базе данных для проведения тестов.")
            
        # Оставляем типы (int) как в реальном коде Aiogram
        self.client_id = user_ids[0]
        self.provider_id = user_ids[1]
        
        self.bot = Bot(token=config.BOT_TOKEN)
        self.moderator_id = config.MODERATOR_CONTACT_ID

        # Находим реальную услугу провайдера из базы профилей
        p_profile = self.profiles.get(str(self.provider_id)) or self.profiles.get(int(self.provider_id)) or {}
        p_services = p_profile.get("services", [])
        if p_services:
            self.service_name = p_services[0].get("name", "Реальная услуга")
            self.price = float(p_services[0].get("price", 50.0))
        else:
            self.service_name = "Услуга (Без названия)"
            self.price = 50.0

    async def asyncTearDown(self):
        """Закрытие сессии бота после завершения каждого теста"""
        await self.bot.session.close()

    def test_database_loaded(self):
        """Проверка успешной загрузки базы данных"""
        self.assertGreater(len(self.users), 0)
        self.assertIsNotNone(self.client_id)
        self.assertIsNotNone(self.provider_id)

    async def test_alert_deal_created_format(self):
        """Тест 1: Проверка форматирования алерта создания новой сделки через боевой alert_formatter"""
        deal_id = "test_deal_12345"

        # Вызываем боевой форматировщик из msgs_utils (SOLID!)
        moderator_text = format_new_deal_alert(
            deal_id=deal_id,
            client_id=self.client_id,
            provider_id=self.provider_id,
            service_name=self.service_name,
            price=self.price,
            users_db=self.users,
            profiles_db=self.profiles
        )

        logging.info(f"👉 Сгенерированный текст Теста 1:\n{moderator_text}\n")

        self.assertIn("Создана новая сделка", moderator_text)
        self.assertIn(str(self.client_id), moderator_text)
        self.assertIn(str(self.provider_id), moderator_text)
        self.assertIn(self.service_name, moderator_text)
        
        # Отправляем тестовый алерт модератору для визуального контроля
        await self.bot.send_message(chat_id=self.moderator_id, text=moderator_text, parse_mode="HTML")
        logging.info("✅ Алерт создания сделки успешно доставлен модератору!")

    async def test_alert_deal_finished_format(self):
        """Тест 2: Проверка форматирования алерта завершения сделки через боевой alert_formatter"""
        deal_id = "test_deal_12345"
        server_commission = round(self.price * 0.1, 2)

        # Вызываем боевой форматировщик из msgs_utils (SOLID!)
        moderator_text = format_deal_completed_alert(
            deal_id=deal_id,
            client_id=self.client_id,
            provider_id=self.provider_id,
            service_name=self.service_name,
            server_commission=server_commission,
            users_db=self.users,
            profiles_db=self.profiles
        )

        logging.info(f"👉 Сгенерированный текст Теста 2:\n{moderator_text}\n")

        self.assertIn("Сделка завершена", moderator_text)
        self.assertIn(str(self.client_id), moderator_text)
        self.assertIn(str(self.provider_id), moderator_text)
        self.assertIn(self.service_name, moderator_text)
        
        await self.bot.send_message(chat_id=self.moderator_id, text=moderator_text, parse_mode="HTML")
        logging.info("✅ Алерт завершения сделки успешно доставлен модератору!")

    async def test_alert_deal_blocked_format(self):
        """Тест 3: Проверка форматирования алерта попытки сделки с заблокированным через боевой alert_formatter"""
        # Вызываем боевой форматировщик из msgs_utils (SOLID!)
        moderator_text = format_deal_blocked_alert(
            client_id=self.client_id,
            provider_id=self.provider_id,
            users_db=self.users,
            profiles_db=self.profiles
        )

        logging.info(f"👉 Сгенерированный текст Теста 3:\n{moderator_text}\n")

        self.assertIn("Попытка начать сделку", moderator_text)
        self.assertIn(str(self.client_id), moderator_text)
        self.assertIn(str(self.provider_id), moderator_text)
        
        await self.bot.send_message(chat_id=self.moderator_id, text=moderator_text, parse_mode="HTML")
        logging.info("✅ Алерт попытки сделки успешно доставлен модератору!")

    async def test_alert_profile_changed_format(self):
        """Тест 4: Проверка форматирования алерта об изменении профиля клиента"""
        diff_text = "📝 <b>Имя</b>: Илья -> Илюха\n💼 <b>Деятельность</b>: Фотограф -> Pro Фотограф"
        moderator_text = format_profile_changed_alert(
            user_id=self.client_id,
            username="test_username_123",
            diff_text=diff_text,
            users_db=self.users,
            profiles_db=self.profiles
        )

        logging.info(f"👉 Сгенерированный текст Теста 4:\n{moderator_text}\n")

        self.assertIn("Клиент хочет изменить профиль", moderator_text)
        self.assertIn(str(self.client_id), moderator_text)
        self.assertIn("Илюха", moderator_text)

        await self.bot.send_message(chat_id=self.moderator_id, text=moderator_text, parse_mode="HTML")
        logging.info("✅ Алерт изменения профиля успешно доставлен модератору!")

    async def test_alert_new_registration_format(self):
        """Тест 5: Проверка форматирования алерта о новой регистрации"""
        services_sample = [
            {"name": self.service_name, "description": "Профессиональная съемка", "price": str(self.price)}
        ]
        moderator_text = format_new_registration_alert(
            user_id=self.client_id,
            username="test_new_user",
            name="Иван Тестов",
            area="Улувату",
            profession="Фотограф",
            desc_prof="Делаю красивые фотосессии на Бали",
            links="instagram.com/test",
            services_list=services_sample,
            users_db=self.users,
            profiles_db=self.profiles
        )

        logging.info(f"👉 Сгенерированный текст Теста 5:\n{moderator_text}\n")

        self.assertIn("Новая заявка на вступление", moderator_text)
        self.assertIn(str(self.client_id), moderator_text)
        self.assertIn("Иван Тестов", moderator_text)
        self.assertIn("Улувату", moderator_text)

        await self.bot.send_message(chat_id=self.moderator_id, text=moderator_text, parse_mode="HTML")
        logging.info("✅ Алерт новой заявки на регистрацию успешно доставлен модератору!")

    async def test_alert_deal_auto_cancelled_format(self):
        """Тест 6: Проверка форматирования алерта авто-отмены сделки по таймауту"""
        deal_id = "timeout_deal_999"
        reason = "Истекло время подтверждения (24ч). Исполнитель не ответил на заявку."
        moderator_text = format_deal_auto_cancelled_alert(
            deal_id=deal_id,
            client_id=self.client_id,
            provider_id=self.provider_id,
            service_name=self.service_name,
            price=self.price,
            reason=reason,
            users_db=self.users,
            profiles_db=self.profiles
        )

        logging.info(f"👉 Сгенерированный текст Теста 6:\n{moderator_text}\n")

        self.assertIn("Авто-отмена сделки по таймауту", moderator_text)
        self.assertIn(str(self.client_id), moderator_text)
        self.assertIn(str(self.provider_id), moderator_text)
        self.assertIn(self.service_name, moderator_text)

        await self.bot.send_message(chat_id=self.moderator_id, text=moderator_text, parse_mode="HTML")
        logging.info("✅ Алерт авто-отмены сделки успешно доставлен модератору!")

    async def test_alert_new_registration_corrupt_data(self):
        """Тест 7: Защита от дурака - проверка форматирования при полностью пустых или некорректных данных анкеты"""
        # Передаем None во все поля и кривой список услуг (некоторые элементы не словари)
        services_corrupt = [
            None,
            "Просто строка вместо словаря услуг",
            {"name": None, "description": "Сломанное описание", "price": None}
        ]
        
        moderator_text = format_new_registration_alert(
            user_id=self.client_id,
            username=None,
            name=None,
            area=None,
            profession=None,
            desc_prof=None,
            links=None,
            services_list=services_corrupt,
            users_db=self.users,
            profiles_db=self.profiles
        )

        logging.info(f"👉 Сгенерированный текст Теста 7 (Защита от дурака):\n{moderator_text}\n")

        self.assertIn("Новая заявка на вступление", moderator_text)
        self.assertIn("Не указано", moderator_text)
        self.assertIn("Некорректный формат услуги", moderator_text)
        
        await self.bot.send_message(chat_id=self.moderator_id, text=moderator_text, parse_mode="HTML")
        logging.info("✅ Тест защиты от дурака успешно пройден и доставлен модератору!")

if __name__ == "__main__":
    unittest.main()
