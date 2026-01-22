import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import datetime
import config
import distribute

class TextHandler:
    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget

    def write(self, msg: str):
        if not msg.strip():
            return
        def append():
            self.text_widget.insert(tk.END, msg + "\n")
            self.text_widget.see(tk.END)
        self.text_widget.after(0, append)

    def flush(self):
        pass

class DistributorApp:
    def __init__(self, root: tk.Tk):
        self.last_report_path = None
        self.root = root
        self.root.title("ArchDistributor — Распределение проектных данных")
        self.center_window(900, 700)
        self.root.minsize(300, 400)

        self.source_folder = tk.StringVar()
        self.target_folder = tk.StringVar()
        self.name_pattern = tk.StringVar(value="GPNG-GEP-RD")
        self.is_running = False
        self.total_files = 0
        self.processed_files = 0

        self.backend_thread = None
        self.backend_stop_flag = False

        self._build_ui()

    def center_window(self, width, height):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        # === Глобальный скроллбар ===
        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.configure(yscrollcommand=scrollbar.set)

        # Фрейм, в котором будет весь UI
        main = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=main, anchor="nw")

        # Адаптивная ширина
        def _resize_main(event):
            canvas.itemconfig(window_id, width=event.width)

        canvas.bind("<Configure>", _resize_main)

        # Авто‑обновление scrollregion
        def _update_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        main.bind("<Configure>", _update_scrollregion)

        # === конец блока ===

        folder_frame = ttk.LabelFrame(main, text="Исходные данные", padding=10)
        folder_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(folder_frame, text="Папка с Нераспределёнными данными:").grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(folder_frame, textvariable=self.source_folder)
        entry.grid(row=1, column=0, sticky="ew", pady=5)
        browse_btn = ttk.Button(folder_frame, text="Обзор...", command=self._choose_folder)
        browse_btn.grid(row=1, column=1, padx=(5, 0))
        folder_frame.columnconfigure(0, weight=1)

        target_frame = ttk.LabelFrame(main, text="Папка назначения", padding=10)
        target_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(target_frame, text="Папка, куда будет создаваться структура РД:").grid(row=0, column=0, sticky="w")
        target_entry = ttk.Entry(target_frame, textvariable=self.target_folder)
        target_entry.grid(row=1, column=0, sticky="ew", pady=5)
        target_btn = ttk.Button(target_frame, text="Обзор...", command=self._choose_target_folder)
        target_btn.grid(row=1, column=1, padx=(5, 0))
        target_frame.columnconfigure(0, weight=1)

        settings_frame = ttk.LabelFrame(main, text="Настройки распределения", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(settings_frame, text="Копировать только файлы, содержащие шаблон:").grid(row=0, column=0, sticky="w")
        pattern_entry = ttk.Entry(settings_frame, textvariable=self.name_pattern, width=40)
        pattern_entry.grid(row=1, column=0, sticky="w", pady=(2, 8))

        ttk.Label(settings_frame, text="Коды проектов:").grid(row=2, column=0, sticky="w", pady=(5, 0))
        ttk.Label(settings_frame, text="003 → Ранние работы\n113 → Основной договор", foreground="gray").grid(row=3, column=0, sticky="w")

        ttk.Label(settings_frame, text="Папки ревизий:").grid(row=0, column=1, sticky="nw", padx=(20, 0))
        ttk.Label(settings_frame, text="• пдф — PDF файлы\n• ред.формат — DOC, XLSX, XLSM, DWG", foreground="gray").grid(row=1, column=1, rowspan=3, sticky="nw", padx=(20, 0))

        control_frame = ttk.Frame(main)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(control_frame, text="Запустить распределение", command=self._on_start)
        self.start_btn.pack(side=tk.LEFT)

        self.stop_btn = ttk.Button(control_frame, text="Остановить", command=self._on_stop, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=(5, 0))

        self.clear_log_btn = ttk.Button(control_frame, text="Очистить лог", command=self._clear_log)
        self.clear_log_btn.pack(side=tk.LEFT, padx=(5, 0))

        self.save_report_btn = ttk.Button(control_frame, text="Сохранить отчёт", command=self._save_report, state="disabled")
        self.save_report_btn.pack(side=tk.LEFT, padx=(5, 0))

        progress_frame = ttk.LabelFrame(main, text="Прогресс", padding=10)
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress_bar.pack(fill=tk.X)

        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(anchor="w", pady=(5, 0))

        self.current_file_label = ttk.Label(progress_frame, text="Текущий файл: —", foreground="gray")
        self.current_file_label.pack(anchor="w", pady=(2, 0))

        stats_frame = ttk.LabelFrame(main, text="Статистика", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        self.stats_text = tk.Text(stats_frame, height=8, wrap="word")
        self.stats_text.pack(fill=tk.X)

        # запрет ввода
        # self.stats_text.bind("<Key>", lambda e: "break")
        # self.stats_text.bind("<Button-3>", lambda e: print("CLICK TEXT"))

        # оформление тега ссылок
        self.stats_text.tag_config("link", foreground="blue", underline=True)
        self.stats_text.bind("<Button-1>", self._on_stats_click)

        log_frame = ttk.LabelFrame(main, text="Лог выполнения", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap="word")
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(main, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        status_bar.pack(fill=tk.X, pady=(5, 0))

        self.text_handler = TextHandler(self.log_text)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # Windows и MacOS
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Linux (если нужно)
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    def _choose_folder(self):
        p = filedialog.askdirectory()
        if p:
            self.source_folder.set(p)
            self.status_var.set(f"Выбрана папка: {Path(p).name}")

    def _choose_target_folder(self):
        p = filedialog.askdirectory()
        if p:
            self.target_folder.set(p)
            self.status_var.set(f"Папка назначения: {Path(p).name}")

    def _on_start(self):
        if self.is_running:
            return

        src = self.source_folder.get().strip()
        if not src:
            messagebox.showwarning("Папка не выбрана", "Выберите папку с Нераспределёнными данными")
            return
        if not Path(src).exists():
            messagebox.showerror("Ошибка", "Указанная папка не существует")
            return

        target = self.target_folder.get().strip()
        if not target:
            messagebox.showwarning("Папка назначения не выбрана", "Выберите папку назначения")
            return
        if not Path(target).exists():
            messagebox.showerror("Ошибка", "Папка назначения не существует")
            return

        pattern = self.name_pattern.get().strip()
        if not pattern:
            messagebox.showwarning("Шаблон пустой", "Укажите шаблон имени файла")
            return

        self._reset_progress()
        self._reset_stats()
        self._log("=== Старт распределения ===")
        self._log(f"Папка: {src}")
        self._log(f"Назначение: {target}")
        self._log(f"Шаблон имени: {pattern}")

        self.is_running = True
        self.backend_stop_flag = False
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.save_report_btn.config(state="disabled")
        self.status_var.set("Распределение запущено...")

        self.backend_thread = threading.Thread(
            target=self._backend_start_wrapper,
            args=(src, target, pattern),
            daemon=True
        )
        self.backend_thread.start()

    def _on_stop(self):
        if not self.is_running:
            return
        self.backend_stop_flag = True
        self._log("Запрошена остановка...")
        self.status_var.set("Остановка...")

    def _clear_log(self):
        self.log_text.delete("1.0", tk.END)
        self._log("Лог очищен")

    def _save_report(self):
        if not hasattr(self, "last_report_path") or not self.last_report_path:
            messagebox.showwarning("Отчёт", "Отчёт ещё не создан.")
            return

        if not os.path.exists(self.last_report_path):
            messagebox.showerror("Ошибка", "Файл отчёта не найден.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv"), ("Все файлы", "*.*")]
        )

        if not file_path:
            return

        try:
            # Если пользователь выбрал .xlsx — конвертируем CSV → XLSX
            if file_path.lower().endswith(".xlsx"):
                import pandas as pd
                df = pd.read_csv(self.last_report_path, sep=";", encoding="utf-8-sig")
                df.to_excel(file_path, index=False)
            else:
                # Иначе просто копируем CSV
                import shutil
                shutil.copy2(self.last_report_path, file_path)

            self._log(f"Отчёт сохранён в: {file_path}")
            messagebox.showinfo("Отчёт", f"Отчёт сохранён в:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении отчёта:\n{e}")
            self._log(f"Ошибка при сохранении отчёта: {e}")

    def _reset_progress(self):
        self.progress_bar["value"] = 0
        self.progress_label.config(text="0%")
        self.current_file_label.config(text="Текущий файл: —")
        self.total_files = 0
        self.processed_files = 0

    def _reset_stats(self):
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert(tk.END, "Статистика появится после завершения.\n")
        # self.stats_text.config(state="disabled")

    def _log(self, msg: str):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.text_handler.write(f"[{ts}] {msg}")

    def update_progress(self, processed: int, total: int, current_file: str | None = None):
        self.processed_files = processed
        self.total_files = max(total, 1)
        value = processed / self.total_files * 100.0
        self.progress_bar["value"] = value
        self.progress_label.config(text=f"{value:.1f}%")
        if current_file:
            self.current_file_label.config(text=f"Текущий файл: {current_file}")
        self.root.update_idletasks()

    def _on_stats_click(self, event):
        index = self.stats_text.index(f"@{event.x},{event.y}")
        line = self.stats_text.get(f"{index} linestart", f"{index} lineend").strip()

        # интересуют только строки вида "• C:/..."
        if not line.startswith("• "):
            return

        path = line.replace("• ", "").strip()
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showerror("Ошибка", f"Файл не найден:\n{path}")

    def _open_conflict_path(self, event):
        index = self.stats_text.index(f"@{event.x},{event.y}")
        line = self.stats_text.get(f"{index} linestart", f"{index} lineend")

        path = line.replace("• ", "").strip()

        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showerror("Ошибка", f"Файл не найден:\n{path}")

    def update_stats(self, stats: dict):
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", tk.END)

        conflicts = stats.get("conflict_files", [])

        lines = [
            f"Файлов обработано: {stats.get('processed', 0)}",
            f"Скопировано: {stats.get('copied', 0)}",
            f"Пропущено (не по шаблону: {config.NAME_PATTERN}): {stats.get('skipped_pattern', 0)}",
            f"Дубликатов: {stats.get('duplicates', 0)}",
            f"Конфликтов имён: {stats.get('conflicts', 0)}",
            f"Ошибок: {stats.get('errors', 0)}",
        ]

        if "report_path" in stats:
            self.last_report_path = stats["report_path"]

        self.stats_text.insert(tk.END, "\n".join(lines))

        if conflicts:
            self.stats_text.insert(tk.END, "\n\nФайлы с конфликтами:\n")
            for path in conflicts:
                self.stats_text.insert(tk.END, f"• {path}\n")

    def _progress_callback(self, processed: int, total: int, current_file: str):
        self.root.after(0, self.update_progress, processed, total, current_file)

    def _stats_callback(self, stats: dict):
        self.root.after(0, self.update_stats, stats)

    def on_backend_finished(self, success: bool, error: str | None = None):
        self.is_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.save_report_btn.config(state="normal")
        if success:
            self.status_var.set("Распределение завершено")
            self._log("=== Распределение завершено ===")
        else:
            self.status_var.set("Ошибка распределения")
            self._log(f"Ошибка распределения: {error or 'неизвестная ошибка'}")
            messagebox.showerror("Ошибка", f"Ошибка при распределении:\n{error or 'неизвестная ошибка'}")

    def _backend_start_wrapper(self, src: str, target: str, pattern: str):
        try:
            config.SOURCE_DIR = src
            config.TARGET_DIR = target
            config.NAME_PATTERN = pattern
            distribute.main(progress_callback=self._progress_callback, stats_callback=self._stats_callback)
            self.root.after(0, self.on_backend_finished, True, None)
        except Exception as e:
            self.root.after(0, self.on_backend_finished, False, str(e))

def main():
    root = tk.Tk()
    app = DistributorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

#TODO:
#Скролл для статистики
#Два конфликтующих файла