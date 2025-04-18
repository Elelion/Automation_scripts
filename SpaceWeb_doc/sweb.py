import os
import time
import logging

from dotenv import load_dotenv

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from cryptography.fernet import Fernet


# **


# Настроим формат для логирования с цветами
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

# делаем работу в браузере скрытой
options = Options()
options.add_argument("--headless")  # Без интерфейса
options.add_argument("--disable-gpu")  # Иногда нужно для Windows
options.add_argument("--window-size=1920,1080")  # рендер как на обычном экране
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-extensions")


# загружаем данные из .env
# оставляем если понадобиться работать БЕЗ шифрования данных, на прямую с .env
# dotenv_path = '.env'
# load_dotenv(dotenv_path)


# -----------------------------------------------------------------------------


def crypto_key_generation_once():
    """
    Описание:
    - создает файл key.key в корне
    - записывает в key.key каждый раз уникальный пароль
    - запускать данную ф-цию лишь единожды для генерации пароля

    wb - write binary
    """

    key = Fernet.generate_key()

    with open('../space_check/111/key.key', 'wb') as f:
        f.write(key)

    print("Ключ сохранен в key.key — НЕ передавать никому!")


def crypto_env_encryption_once():
    """
    Описание:
    - шифрует ключ key.key
    - перезаписывает key.key уже в шифрованном виде

    rb - read binary
    """
    with open('../space_check/111/key.key', 'rb') as key_file:
        key = key_file.read()
        fernet = Fernet(key)  # создаем объект для шифрования с указанным ключом

        with open('.env', 'rb') as file:
            original = file.read()

        encrypted = fernet.encrypt(original)  # шифруем

        with open('../space_check/111/.env.enc', 'wb') as encrypted_file:
            encrypted_file.write(encrypted)  # сохраняем зашифрованный вариант

    print("✅ .env зашифрован → .env.enc")


def decryption_env_key():
    """
    Описание:
    - берем key.key
    - извлекаем ключ
    - с ключом расшифровываем .env.enc
    - расшифрованные данные заносим в память -> os.environ[key] = value

    decrypt(encrypted).decode():
    - decrypt(encrypted) — расшифровывает байты
    - .decode() — превращает результат из байтов в строку
    """

    with open('../space_check/111/key.key', 'rb') as key_file:
        key = key_file.read()

    fernet = Fernet(key)

    with open('../space_check/111/.env.enc', 'rb') as enc_file:
        encrypted = enc_file.read()

    decrypted = fernet.decrypt(encrypted).decode()

    # парсинг построчно в переменные окружения
    for line in decrypted.splitlines():
        if '=' in line:
            key, value = line.strip().split('=', 1)
            os.environ[key] = value


# -----------------------------------------------------------------------------


def initialize_driver():
    driver = webdriver.Chrome(options=options)
    driver.get('https://sweb.ru/')
    driver.maximize_window()
    return driver


def login(driver, login, psw, dashboard_url):
    """
    ШАГ1: авторизация

    Описание:
    - заходим на сайт
    - заполняем логин / пароль
    - кликаем на кнопку входа
    """

    control_panel_button = driver.find_element(By.XPATH, '//a[@title="Панель управления"]')
    driver.execute_script('arguments[0].click();', control_panel_button)
    print('Заходим в Панель управления')
    time.sleep(3)

    # login & password
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.NAME, 'login'))).send_keys(login)
    wait.until(EC.presence_of_element_located((By.NAME, 'password'))).send_keys(psw)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input.submit'))).click()
    print('логин введен | пароль введен | Войти - нажата')

    # проверяем редирект на dashboard
    try:
        WebDriverWait(driver, 15).until(EC.url_to_be(dashboard_url))
        logging.info('✅ Редирект в панель управления - успех')
    except TimeoutException:
        logging.error('❌ Не дождались редиректа — что-то пошло не так')
        driver.quit()
        exit()


def navigating_to_the_download(driver):
    """
    ШАГ2: кликаем до загрузки документов

    Описание:
    - идем по требуемым разделам до раздела с загрузкой документов
    """

    # Нажимаем на "Аккаунт"
    # account_button = driver.find_element(By.CSS_SELECTOR, 'a[data-title="Аккаунт"]')
    # driver.execute_script('arguments[0].click();', account_button)

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-title="Аккаунт"]'))
    ).click()
    print('Аккаунт - выбран')

    # Нажимаем на "Финансы"
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.NAME, 'finance'))
    ).click()
    print('Финансы - выбран')

    # Нажимаем вкладку "Документы"
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//button[text()="Документы"]'))
    ).click()
    print('Вкладка документы - выбран')


# **

def request_acts_and_invoices(driver):
    """
    Описание:
    - Нажимаем на "Запросить архив, pdf" для Актов
    - Нажимаем на "Запросить архив, pdf" для Счет-фактур
    - Проверяем сформировались ли архивы для загрузки или нет
    """

    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//a[contains(@class, "link") and contains(text(), "Запросить архив")]'))
    ).click()
    print('Акты - запрашиваем архив в pdf')
    time.sleep(1)

    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '(//a[contains(@class, "link") and contains(text(), "Запросить архив")])[1]'))
    ).click()
    time.sleep(1)
    print('Счет фактура - запрашиваем архив в pdf')

    try:
        WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//a[contains(@class, "link") and contains(text(), "Сохранить все")]')))
        logging.info('✅ Файлы успешно сформированы к загрузке')
        time.sleep(3)
    except TimeoutException:
        logging.error('❌ Файлы НЕ удалось сформировать — что-то пошло не так')
        driver.quit()
        exit()


def download_acts_and_invoices(driver):
    """
    Описание:
    - Нажимаем на "Сохранить все, pdf" для запрошенных ранее Актов
    - Нажимаем на "Сохранить все, pdf" для запрошенных ранее Счет-фактур
    """

    driver.find_element(By.XPATH, '//a[contains(@class, "link") and contains(text(), "Сохранить все")]').click()
    print('Акты - загружаем...')
    time.sleep(3)

    driver.find_element(By.XPATH, '(//a[contains(@class, "link") and contains(text(), "Сохранить все")])[2]').click()
    print('Счет фактура - загружаем...')
    time.sleep(3)

    logging.info('Файлы успешно загружены в ЗАГРУЗКИ')


def request_reconciliation_report(driver):
    """
    Описание:
    - Заходим в раздел Акт сверки
    - Запрашиваем Акт сверки за текущий год
    """

    driver.find_element(By.XPATH, '//a[@href="/account/finance/act_reconciliation"]/button[contains(text(), "Акт сверки")]').click()
    print('Акт сверки запрошен')
    time.sleep(5)

    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "yearnow"))
    ).click()


def download_reconciliation_report(driver):
    """
    Описание:
    - скачиваем акт сверки за текущий год
    """

    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//button[text()="Скачать, pdf"]'))
    ).click()
    print('Акт сверки за текущий год загружен')


def download_documents(driver):
    """
    ШАГ3: загружаем документы

    Описание:
    - запрашиваем Акты и Счет-фактуры за текущий год: request_acts_and_invoices()
    - скачиваем Акты и Счет-фактуры: download_acts_and_invoices()
    - запрашиваем акт сверки за текущий год: request_reconciliation_report()
    - скачиваем акт сверки за текущий год
    """

    request_acts_and_invoices(driver)
    download_acts_and_invoices(driver)
    request_reconciliation_report(driver)
    download_reconciliation_report(driver)


# -----------------------------------------------------------------------------


def main():
    driver = initialize_driver()

    try:
        username = os.getenv('SWEB_LOGIN')
        password = os.getenv('SWEB_PASSWORD')
        dashboard_url = 'https://cp.sweb.ru/main'

        login(driver, username, password, dashboard_url)
        time.sleep(5)

        navigating_to_the_download(driver)
        time.sleep(5)

        download_documents(driver)
        time.sleep(5)

    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")

    finally:
        driver.quit()
        logging.info("Работа завершена")


# **


if __name__ == "__main__":
    start_time = time.time()

    # **

    # для генерации ключа
    # crypto_key_generation_once()

    # для шифрования ключа
    # crypto_env_encryption_once()

    # **

    decryption_env_key()
    main()

    end_time = time.time()
    print(f"Время выполнения: {end_time - start_time:.2f} секунд")
