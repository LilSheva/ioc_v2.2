"""
Модуль для автоматического сохранения вложений из непрочитанных писем Outlook
и отметки их как прочитанных.
"""

import os
import sys

# ==============================================================================
# НАСТРОЙКИ / CONFIGURATION
# ==============================================================================
# Локальная папка для сохранения вложений.
# Будет создана автоматически, если не существует.
SAVE_DIR = r"C:\ioc\outlook_attachments"

# Имя папки в Outlook для поиска писем.
# Если пусто (None или ""), используется папка "Входящие" по умолчанию (Inbox, GetDefaultFolder(6)).
# Поиск выполняется сначала во входящих, затем рекурсивно по всем папкам.
FOLDER_NAME = ""

# Разрешать ли переименование файлов при совпадении имен?
# True: добавляет суффикс (например, file_1.xlsx), если файл с таким именем уже существует.
# False: перезаписывает существующие файлы.
PRESERVE_EXISTING_FILES = True

# Включить подробный вывод логов в консоль
VERBOSE = True
# ==============================================================================


def find_folder_recursive(root_folder, target_name):
    """
    Рекурсивный поиск папки по имени в структуре папок Outlook.
    """
    if root_folder.Name.lower() == target_name.lower():
        return root_folder
    
    for subfolder in root_folder.Folders:
        found = find_folder_recursive(subfolder, target_name)
        if found:
            return found
    return None


def get_outlook_folder(namespace, folder_name):
    """
    Возвращает папку Outlook (объект Folder).
    Если имя не задано, возвращает папку по умолчанию "Входящие" (Inbox).
    """
    inbox = namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
    
    if not folder_name:
        if VERBOSE:
            print("📁 Папка не указана. Используется папка по умолчанию: 'Входящие'")
        return inbox
    
    # 1. Пробуем найти как прямую подпапку во "Входящих"
    try:
        return inbox.Folders[folder_name]
    except Exception:
        pass
    
    # 2. Ищем рекурсивно во "Входящих"
    found = find_folder_recursive(inbox, folder_name)
    if found:
        return found
        
    # 3. Ищем рекурсивно по всем почтовым ящикам/хранилищам
    if VERBOSE:
        print(f"🔍 Папка '{folder_name}' не найдена во 'Входящих'. Запуск глобального поиска...")
    for store_folder in namespace.Folders:
        found = find_folder_recursive(store_folder, folder_name)
        if found:
            return found
            
    raise ValueError(f"❌ Папка '{folder_name}' не найдена в Outlook.")


def process_outlook_attachments():
    """
    Основная логика: подключение к Outlook, поиск непрочитанных писем,
    сохранение вложений и отметка писем как прочитанных.
    """
    try:
        import win32com.client
    except ImportError:
        print("❌ Ошибка: не установлена библиотека pywin32.")
        print("Пожалуйста, установите её командой: pip install pywin32")
        return False

    if VERBOSE:
        print("🔌 Подключение к Outlook...")
        
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        namespace = outlook.GetNameSpace("MAPI")
    except Exception as e:
        print(f"❌ Не удалось подключиться к Outlook: {e}")
        print("Убедитесь, что Outlook запущен и настроен.")
        return False

    try:
        folder = get_outlook_folder(namespace, FOLDER_NAME)
        if VERBOSE:
            print(f"✅ Успешно подключились к папке: '{folder.Name}'")
    except Exception as e:
        print(str(e))
        return False

    # Получаем элементы папки
    items = folder.Items
    
    # Ограничиваем выборку только непрочитанными письмами
    # Фильтр [Unread] = true
    try:
        unread_items = items.Restrict("[Unread] = true")
    except Exception as e:
        print(f"❌ Ошибка применения фильтра непрочитанных писем: {e}")
        return False

    count_unread = unread_items.Count
    if VERBOSE:
        print(f"📩 Найдено непрочитанных писем: {count_unread}")

    if count_unread == 0:
        if VERBOSE:
            print("📭 Нет новых непрочитанных писем для обработки.")
        return True

    # Создаем директорию для сохранения, если её нет
    if not os.path.exists(SAVE_DIR):
        try:
            os.makedirs(SAVE_DIR)
            if VERBOSE:
                print(f"📂 Создана директория для сохранения: {SAVE_DIR}")
        except Exception as e:
            print(f"❌ Ошибка создания папки {SAVE_DIR}: {e}")
            return False

    processed_emails_count = 0
    saved_attachments_count = 0

    # Создаем копию списка писем, так как при изменении статуса Unread внутри цикла
    # коллекция unread_items в Outlook может динамически перестраиваться.
    email_list = list(unread_items)

    for i, mail in enumerate(email_list, 1):
        # Проверяем, является ли элемент письмом и имеет ли необходимые атрибуты
        if not hasattr(mail, "Attachments") or not hasattr(mail, "UnRead"):
            continue
            
        subject = getattr(mail, "Subject", "Без темы")
        attachments_count = mail.Attachments.Count

        if VERBOSE:
            print(f"\n📧 [{i}/{len(email_list)}] Письмо: '{subject}'")
            print(f"   Вложений: {attachments_count}")

        if attachments_count > 0:
            for attachment in mail.Attachments:
                orig_filename = attachment.FileName
                save_path = os.path.join(SAVE_DIR, orig_filename)
                
                # Разрешение конфликтов имен
                if PRESERVE_EXISTING_FILES and os.path.exists(save_path):
                    base, ext = os.path.splitext(orig_filename)
                    counter = 1
                    while os.path.exists(save_path):
                        new_filename = f"{base}_{counter}{ext}"
                        save_path = os.path.join(SAVE_DIR, new_filename)
                        counter += 1
                    final_filename = os.path.basename(save_path)
                else:
                    final_filename = orig_filename

                try:
                    attachment.SaveAsFile(save_path)
                    saved_attachments_count += 1
                    if VERBOSE:
                        print(f"   💾 Сохранено: {final_filename}")
                except Exception as e:
                    print(f"   ❌ Не удалось сохранить вложение {orig_filename}: {e}")

        # Снимаем флаг непрочитанного и сохраняем изменения в Outlook
        try:
            mail.UnRead = False
            mail.Save()
            processed_emails_count += 1
            if VERBOSE:
                print("   ✔ Отмечено как прочитанное")
        except Exception as e:
            print(f"   ❌ Не удалось отметить письмо как прочитанное: {e}")

    if VERBOSE:
        print("\n" + "=" * 50)
        print("📊 ИТОГИ ОБРАБОТКИ:")
        print(f"   Обработано писем: {processed_emails_count}")
        print(f"   Сохранено вложений: {saved_attachments_count}")
        print(f"   Путь сохранения: {SAVE_DIR}")
        print("=" * 50)

    return True


if __name__ == "__main__":
    process_outlook_attachments()
