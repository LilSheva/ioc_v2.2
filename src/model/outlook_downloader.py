"""
Модуль для автоматического скачивания писем и вложений из Outlook.
"""

import os


class OutlookDownloader:
    """Класс для работы с почтой Outlook через COM-интерфейс MAPI."""

    def __init__(self, settings: dict):
        """
        Инициализация загрузчика.

        Args:
            settings: Словарь настроек приложения (из settings.json)
        """
        self.outlook_folder = settings.get("outlook_folder", "")
        self.save_dir = settings.get("save_dir", r"C:\ioc\outlook_attachments")
        self.preserve_existing_files = settings.get("preserve_existing_files", True)
        self.verbose = settings.get("verbose", True)

    def log(self, message: str, callback=None):
        """Логирование сообщения в консоль и коллбек."""
        if self.verbose:
            print(message)
        if callback:
            callback(message)

    def find_folder_recursive(self, root_folder, target_name):
        """Рекурсивный поиск папки по имени."""
        if root_folder.Name.lower() == target_name.lower():
            return root_folder
        
        for subfolder in root_folder.Folders:
            found = self.find_folder_recursive(subfolder, target_name)
            if found:
                return found
        return None

    def get_outlook_folder(self, namespace, log_callback=None):
        """Возвращает папку Outlook (объект Folder)."""
        inbox = namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
        
        if not self.outlook_folder:
            self.log("📁 Папка Outlook не указана. Используется папка по умолчанию: 'Входящие'", log_callback)
            return inbox
        
        # 1. Пробуем найти как прямую подпапку во "Входящих"
        try:
            return inbox.Folders[self.outlook_folder]
        except Exception:
            pass
        
        # 2. Ищем рекурсивно во "Входящих"
        found = self.find_folder_recursive(inbox, self.outlook_folder)
        if found:
            return found
            
        # 3. Ищем рекурсивно по всем почтовым ящикам/хранилищам
        self.log(f"🔍 Папка '{self.outlook_folder}' не найдена во 'Входящих'. Запуск глобального поиска...", log_callback)
        for store_folder in namespace.Folders:
            found = self.find_folder_recursive(store_folder, self.outlook_folder)
            if found:
                return found
                
        raise ValueError(f"❌ Папка '{self.outlook_folder}' не найдена в Outlook.")

    def download_attachments(self, log_callback=None) -> list:
        """
        Подключается к Outlook, находит непрочитанные письма, скачивает их вложения
        и сохраняет сами письма в формате .msg в уникальные временные папки.
        Возвращает список словарей с метаданными и путями к сохраненным файлам.
        """
        try:
            import win32com.client
        except ImportError:
            self.log("❌ Ошибка: не установлена библиотека pywin32.", log_callback)
            return []

        self.log("🔌 Подключение к Outlook...", log_callback)
        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNameSpace("MAPI")
        except Exception as e:
            self.log(f"❌ Не удалось подключиться к Outlook: {e}", log_callback)
            return []

        try:
            folder = self.get_outlook_folder(namespace, log_callback)
            self.log(f"✅ Успешно подключились к папке: '{folder.Name}'", log_callback)
        except Exception as e:
            self.log(str(e), log_callback)
            return []

        items = folder.Items
        try:
            unread_items = items.Restrict("[Unread] = true")
        except Exception as e:
            self.log(f"❌ Ошибка применения фильтра непрочитанных писем: {e}", log_callback)
            return []

        count_unread = unread_items.Count
        self.log(f"📩 Найдено непрочитанных писем: {count_unread}", log_callback)

        if count_unread == 0:
            return []

        # Создаем базовую директорию для сохранения, если её нет
        if not os.path.exists(self.save_dir):
            try:
                os.makedirs(self.save_dir)
                self.log(f"📂 Создана директория для сохранения: {self.save_dir}", log_callback)
            except Exception as e:
                self.log(f"❌ Ошибка создания папки {self.save_dir}: {e}", log_callback)
                return []

        import random
        import string
        from datetime import datetime
        
        email_records = []
        email_list = list(unread_items)

        for i, mail in enumerate(email_list, 1):
            if not hasattr(mail, "Attachments") or not hasattr(mail, "UnRead"):
                continue
                
            subject = getattr(mail, "Subject", "Без темы")
            attachments_count = mail.Attachments.Count
            received_time = getattr(mail, "ReceivedTime", None)

            self.log(f"📧 [{i}/{len(email_list)}] Письмо: '{subject}' (вложений: {attachments_count})", log_callback)

            # Создаем уникальную временную папку для этого письма
            rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            time_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            email_temp_dir = os.path.join(self.save_dir, f"temp_{time_str}_{rand_suffix}")
            
            try:
                os.makedirs(email_temp_dir, exist_ok=True)
            except Exception as e:
                self.log(f"   ❌ Ошибка создания временной папки {email_temp_dir}: {e}", log_callback)
                continue

            saved_attachments = []
            msg_path = None

            # 1. Сохраняем само письмо в формате .msg (olMSG = 3)
            import re
            safe_subject = re.sub(r'[\\/*?:"<>|]', '_', subject)
            # Ограничим длину имени файла
            safe_subject = safe_subject[:100]
            msg_filename = f"{safe_subject}.msg"
            msg_path = os.path.join(email_temp_dir, msg_filename)
            
            try:
                mail.SaveAs(msg_path, 3) # 3 = olMSG
                self.log(f"   💾 Письмо сохранено как: {msg_filename}", log_callback)
            except Exception as e:
                self.log(f"   ❌ Ошибка сохранения письма как .msg: {e}", log_callback)
                # Если не удалось сохранить .msg, продолжим, но путь останется None

            # 2. Сохраняем вложения
            if attachments_count > 0:
                for attachment in mail.Attachments:
                    filename = attachment.FileName
                    save_path = os.path.join(email_temp_dir, filename)
                    
                    if self.preserve_existing_files and os.path.exists(save_path):
                          base, ext = os.path.splitext(filename)
                          counter = 1
                          while os.path.exists(save_path):
                              save_path = os.path.join(email_temp_dir, f"{base}_{counter}{ext}")
                              counter += 1
                      
                    try:
                        attachment.SaveAsFile(save_path)
                        saved_attachments.append(save_path)
                        self.log(f"   💾 Сохранено вложение: {os.path.basename(save_path)}", log_callback)
                    except Exception as e:
                        self.log(f"   ❌ Ошибка сохранения вложения {filename}: {e}", log_callback)

            email_records.append({
                "mail_item": mail,
                "received_time": received_time,
                "subject": subject,
                "temp_dir": email_temp_dir,
                "msg_path": msg_path,
                "attachments": saved_attachments
            })

        return email_records
