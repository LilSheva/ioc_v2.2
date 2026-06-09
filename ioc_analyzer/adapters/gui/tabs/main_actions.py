"""
Логика запуска парсинга и генерации отчетов для вкладки "Главная".
"""

import os
from tkinter import filedialog, messagebox, END, NORMAL, DISABLED
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

    if not success or not ioc_data:
        tab_obj.log("\nОбработка завершилась с ошибкой.")
        messagebox.showerror("Ошибка", "Не удалось извлечь IOC из файлов.")
        return

    total_iocs = sum(len(iocs) for iocs in ioc_data.values())
    if total_iocs == 0:
        tab_obj.log("\nВ документах не найдено ни одного IOC.")
        messagebox.showinfo("Информация", "В выбранных документах не найдено ни одного IOC.")
        return

    default_filename = tab_obj.controller.generate_report_filename()

    output_path = filedialog.asksaveasfilename(
        title="Сохранить отчет как...",
        defaultextension=".xlsx",
        filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
        initialfile=default_filename
    )

    if not output_path:
        tab_obj.log("\nСохранение отменено пользователем.")
        return

    success, _ = tab_obj.controller.generate_reports(
        ioc_data, output_path, log_callback=tab_obj.log
    )

    filter_filename = tab_obj.controller.generate_filters_filename()
    filters_path = os.path.join(os.path.dirname(output_path), filter_filename)

    if success:
        tab_obj.log("\n" + "=" * 70)
        tab_obj.log("ОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО")
        tab_obj.log("=" * 70 + "\n")

        message_parts = [
            "Отчёты успешно созданы!",
            "",
            f"  • {os.path.basename(output_path)}"
        ]
        if filters_path and os.path.exists(filters_path):
            message_parts.append(f"  • {os.path.basename(filters_path)}")

        bdu_data = tab_obj.controller.last_bdu_data
        if bdu_data:
            base_name = os.path.splitext(output_path)[0]
            # Отчет CVE генерируется как Excel-файл (с префиксом CVE) в той же папке
            cve_filename = tab_obj.controller.generate_cve_filename()
            cve_path = os.path.join(os.path.dirname(output_path), cve_filename)
            if os.path.exists(cve_path):
                message_parts.append(f"  • {cve_filename} ({len(bdu_data)} BDU-идентификаторов)")

        # Подсчет IP для вывода информации
        ip_block_count = 0
        if ioc_data:
            ip_list = ioc_data.get('IP', [])
            for ioc in ip_list:
                if mode == "fstek" or ioc.status == "block":
                    ip_block_count += 1

        unblock_data = tab_obj.controller.get_last_unblock_data()
        ip_unblock_count = 0
        if mode == "gossopka" and unblock_data:
            ip_unblock_count = len(unblock_data.get('IP', []))

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
        message_parts.append("Открыть .xlsx отчёт?")

        result = messagebox.askyesno("Успех", "\n".join(message_parts))
        if result:
            try:
                os.startfile(output_path)
            except Exception:
                import subprocess
                try:
                    subprocess.run(['xdg-open', output_path])
                except Exception:
                    tab_obj.log("Не удалось автоматически открыть файл.")
    else:
        messagebox.showerror("Ошибка", "Произошла ошибка при генерации отчетов.")
