import sys
import os
import subprocess
import datetime
import smtplib

from typing import Final
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# цвета
RESET_COLOR: Final = "\033[0m"
RED_COLOR: Final = "\033[31m"
GREEN_COLOR: Final = "\033[32m"
YELLOW_COLOR: Final = "\033[33m"
BLUE_COLOR: Final = "\033[34m"

# шрифт
RESET_TEXT_ATTRIBUTES: Final = "\033[0m"
BOLD_TEXT: Final = "\033[1m"

# -----------------------------------------------------------------------------

def printColorText(str, color, bold = False):
    attributes = BOLD_TEXT if bold else RESET_TEXT_ATTRIBUTES
    print(attributes + color + str + RESET_COLOR)

# **

class Backup():
    """
    Класс для автоматизации резервных копий: class Automation()

    Атрибуты:
    rar_path - путь до архиватора WinRAR
    target_path - путь до папки которую будем архивировать
    rar_psw - пароль для создаваемого архива
    target_nas - ip куда будем сохранять создаваемый архив
    target_to_backup - путь на ресурсе, куда следует ложить архив
    target_to_backup_name - имя архива

    mail_sender_login = имя пользователя для отправки писем (те от кого будет отправка)
    mail_sender_password =  пароль для пользователя (см выше)
    mail_receiver_address = куда отправляем
    mail_subject = тема письма
    mail_body = тело письма

    file_path (str) - путь до файла с настройками (settings.conf)
    settings{} - словарь содержащий все атрибуты

    Методы:
    run() - запускает цепочку событий, отвечающие за создание резервных копий
    """

    rar_path = ''
    rar_psw = ''

    target_path = ''
    target_nas = ''
    target_to_backup = ''
    target_to_backup_name = ''

    mail_sender_login = ''
    mail_sender_password = ''
    mail_receiver_address = ''
    mail_subject = ''
    mail_body = ''

    file_path = ''
    settings = {}

    # **

    def __init__(self, file_path):
        # Получаем полный путь до текущей папки, где находится файл file_path
        self.file_path = os.path.join(os.path.dirname(__file__), file_path)
        print("Загружаем конфиг из:", self.file_path)

    def _load_settings(self):
        with open(self.file_path, 'r') as file:
            for line in file:
                line = line.strip()  # Удаляем лишние пробелы и символы перевода строки

                if line and not line.startswith('#'):  # Пропускаем пустые строки и комментарии
                    key, value = line.split('=')  # Разделяем ключ и значение
                    key = key.strip()  # Удаляем лишние пробелы в ключе
                    value = value.strip()  # Удаляем лишние пробелы в значении
                    self.settings[key] = value  # Добавляем ключ и значение в словарь settings

    def _apply_settings(self):
        self.rar_path = self.settings.get('rar_path')
        self.rar_psw = self.settings.get('rar_psw')

        self.target_path = self.settings.get('target_path')
        self.target_nas = self.settings.get('target_nas')
        self.target_to_backup = self.settings.get('target_to_backup')
        self.target_to_backup_name = self.settings.get('target_to_backup_name')

        self.mail_sender_login = self.settings.get('mail_sender_login')
        self.mail_sender_password = self.settings.get('mail_sender_password')
        self.mail_receiver_address = self.settings.get('mail_receiver_address')
        self.mail_subject = self.settings.get('mail_subject')
        self.mail_body = self.settings.get('mail_body')

    # Функция subprocess.call(command) в модуле subprocess используется для вызова
    # команды во внешней системе, указанной в command. Она запускает указанную
    # команду и ожидает ее завершения.
    def _backup(self):
        winrar_path = f"{self.rar_path}"
        current_date = datetime.datetime.now().strftime("%d.%m.%Y")
        
        output_file = r"\\{}\{}\{}-{}.rar".format(
            self.target_nas,
            self.target_to_backup,
            self.target_to_backup_name,
            current_date)
        output_file = output_file.replace('"', '')
        print("output_file:", output_file)

        source_dir = f"{self.target_path}"

        command = [winrar_path, "a", "-r", "-m5", f"-p{self.rar_psw}", output_file, source_dir]
        subprocess.call(command)

    # что бы отправлять почту с gmail, нужно предварительно создать специальный
    # логин/пароль для приложений
    # https://support.google.com/accounts/answer/185833?visit_id=638093045649618309-3914306815&p=InvalidSecondFactor&rd=1
    def _send_email(self, sender_email, sender_password, receiver_email, subject, body):
        try:
            # Создание объекта MIMEText
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = subject

            # Добавление текста письма в объект MIMEText
            msg.attach(MIMEText(body, 'plain'))

            # Установка соединения с SMTP-сервером
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()

            # Авторизация на сервере
            server.login(sender_email, sender_password)

            # Отправка письма
            server.sendmail(sender_email, receiver_email, msg.as_string())

            # Закрытие соединения с сервером
            server.quit()
            print("Письмо успешно отправлено!")
        except Exception as e:
            print("Ошибка при отправке письма:", e)

    def run(self):
        self._load_settings()
        self._apply_settings()

        # **

        print("Начинаем создавать резервную копию")
        self._backup()

        print(self.rar_path)
        print(self.target_path)
        print(self.rar_psw)
        print(self.target_nas)
        print("Резервная копия успешно создана")

        # **

        print("Начинаем отправлять отчет на почту")

        self._send_email(self.mail_sender_login,
                         self.mail_sender_password,
                         self.mail_receiver_address,
                         self.mail_subject,
                         self.mail_body)

        print("Отчет успешно отправлен")

# -----------------------------------------------------------------------------

if __name__ == '__main__':
    printColorText("Automation - BackUp", YELLOW_COLOR, True)

    backup = Backup("settings.conf")
    printColorText(backup.__doc__, GREEN_COLOR)
    backup.run()

    print("Все задачи завершены... Выход...")
    sys.exit()  # Завершение программы
