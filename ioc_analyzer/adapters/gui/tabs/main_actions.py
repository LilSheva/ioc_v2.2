"""
Логика запуска парсинга и генерации отчетов для вкладки "Главная".
"""

import os
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk


def run_generation_flow(tab_obj) -> None:
    """Выполняет полный цикл генерации отчетов по нажатию кнопки."""
    if not tab_obj.controller.get_selected_files():
        messagebox.showwarning("Предупреждение", "Не выбраны файлы для обработки!")
        return

    bulletin = tab_obj.bulletin_entry.get().strip()
    tab_obj.controller.set_bulletin(bulletin)

    mode = tab_obj.mode_var.get()
    tab_obj.controller.set_mode(mode)

    uri_clean_mode = tab_obj.uri_clean_var.get()
    tab_obj.controller.set_uri_clean_mode(uri_clean_mode)

    tab_obj.log("\n" + "=" * 70)
    tab_obj.log("ЗАПУСК ОБРАБОТКИ")
    tab_obj.log("=" * 70)
    tab_obj.log(f"Режим: {mode.upper()}")
    tab_obj.log(f"Очистка URI: {'уникальный префикс' if uri_clean_mode == 'unique' else 'только домен'}")
    if mode == "fstek" and bulletin:
        tab_obj.log(f"Бюллетень: {bulletin}")

    success, ioc_data = tab_obj.controller.process_files(log_callback=tab_obj.log)

    if not success:
        tab_obj.log("\nОбработка завершилась с ошибкой.")
        messagebox.showerror("Ошибка", "Не удалось обработать файлы.")
        return

    ioc_data = ioc_data or {}
    bdu_data = tab_obj.controller.last_bdu_data
    total_iocs = sum(len(iocs) for iocs in ioc_data.values())

    if total_iocs == 0 and not bdu_data:
        tab_obj.log("\nВ документах не найдено ни IOC, ни BDU.")
        messagebox.showinfo("Информация", "В выбранных документах не найдено ни IOC, ни BDU.")
        return

    parent_dir = filedialog.askdirectory(
        title="Выберите папку — внутри будет создана структура бюллетеня (Задача / Отчет / Шаблоны IOC)"
    )

    if not parent_dir:
        tab_obj.log("\nСохранение отменено пользователем.")
        return

    success, layout = tab_obj.controller.generate_reports_mailbox(
        ioc_data, parent_dir, log_callback=tab_obj.log
    )

    if success and layout:
        tab_obj.log("\n" + "=" * 70)
        tab_obj.log("ОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО")
        tab_obj.log("=" * 70 + "\n")

        report_files = []
        if os.path.isdir(layout.report):
            report_files = sorted(
                f for f in os.listdir(layout.report)
                if f.lower().endswith(".xlsx")
            )

        message_parts = [
            "Структура папок создана:",
            "",
            f"  {layout.root}",
            "",
            "Отчёты:",
        ]
        for name in report_files:
            message_parts.append(f"  • {name}")

        csv_dir = layout.templates
        if os.path.isdir(csv_dir):
            csv_files = [f for f in os.listdir(csv_dir) if f.lower().endswith(".csv")]
            for name in sorted(csv_files):
                message_parts.append(f"  • Шаблоны IOC/{name}")

        ip_block_count = 0
        if ioc_data:
            ip_list = ioc_data.get("IP", [])
            for ioc in ip_list:
                if mode == "fstek" or ioc.status == "block":
                    ip_block_count += 1

        unblock_data = tab_obj.controller.get_last_unblock_data()
        ip_unblock_count = 0
        if mode == "gossopka" and unblock_data:
            ip_unblock_count = len(unblock_data.get("IP", []))

        if ip_block_count > 0 or ip_unblock_count > 0:
            message_parts.append("")

        if ip_block_count > 0:
            message_parts.append(
                f"⚠ Найдено {ip_block_count} IP-адресов на блокировку.\n"
                f"  Перейдите на вкладку «IP управление»."
            )
        if ip_unblock_count > 0:
            message_parts.append(
                f"ℹ Найдено {ip_unblock_count} IP-адресов на разблокировку.\n"
                f"  Подробнее — во вкладке «IP управление»."
            )

        message_parts.append("")
        message_parts.append("Открыть папку с результатами?")

        result = messagebox.askyesno("Успех", "\n".join(message_parts))
        if result:
            open_dir = os.path.normpath(layout.root)
            try:
                os.startfile(open_dir)
            except OSError:
                tab_obj.log("Не удалось автоматически открыть папку.")
    else:
        messagebox.showerror("Ошибка", "Произошла ошибка при генерации отчетов.")
