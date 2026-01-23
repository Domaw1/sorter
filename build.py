import PyInstaller.__main__
import os
import shutil
from pathlib import Path
from datetime import datetime


def build_exe():
    """Сборка проекта в EXE файл с версией, иконкой и ресурсами."""

    # Версия приложения
    APP_VERSION = "1.0"
    APP_NAME = f"Sorter_v{APP_VERSION}"
    ICON_PATH = "Icon.ico"

    print("🚀 Начинаем сборку EXE файла...")
    print("=" * 60)
    print(f"📋 Версия: {APP_VERSION}")
    print(f"📁 Имя приложения: {APP_NAME}")

    # Папка Releases
    releases_dir = Path("Releases")
    releases_dir.mkdir(exist_ok=True)
    print(f"📂 Папка Releases: {releases_dir.absolute()}")

    # Очистка предыдущих сборок
    for folder in ("build", "dist"):
        p = Path(folder)
        if p.exists():
            shutil.rmtree(p)
            print(f"🧹 Очищена папка {folder}")

    # Параметры PyInstaller
    build_params = [
        "main.py",
        "--onefile",
        "--windowed",
        f"--name={APP_NAME}",
        "--clean",
        "--noconfirm",

        # Включаем ресурсы
        "--add-data=utils;utils",
        "--add-data=reports;reports",
        "--add-data=config.py;.",

        # Скрытые импорты (если нужны)
        "--hidden-import=openpyxl",
        "--hidden-import=openpyxl.styles",
        "--hidden-import=openpyxl.workbook",
        "--hidden-import=dateutil",
        "--hidden-import=pytz",
    ]

    # Иконка
    if Path(ICON_PATH).exists():
        build_params.append(f"--icon={ICON_PATH}")
        print(f"🖼 Используется иконка: {ICON_PATH}")
    else:
        print("⚠️ Иконка не найдена, используется стандартная")

    print("\n📦 Параметры сборки:")
    for p in build_params:
        print("   ", p)

    print("\n⏳ Сборка может занять несколько минут...")
    print("=" * 60)

    try:
        PyInstaller.__main__.run(build_params)

        # Путь к собранному exe
        source_exe = Path("dist") / f"{APP_NAME}.exe"

        if source_exe.exists():
            current_date = datetime.now().strftime("%Y%m%d")
            final_name = f"{APP_NAME}_{current_date}.exe"
            final_path = releases_dir / final_name

            shutil.copy2(source_exe, final_path)

            print("\n🎉 СБОРКА УСПЕШНО ЗАВЕРШЕНА!")
            print("=" * 60)
            print(f"📁 Исходный EXE: {source_exe.absolute()}")
            print(f"📁 Финальный EXE: {final_path.absolute()}")
            print(f"📏 Размер: {final_path.stat().st_size / (1024 * 1024):.2f} MB")

            # Файл информации
            info_file = releases_dir / f"build_info_{APP_VERSION}_{current_date}.txt"
            with open(info_file, "w", encoding="utf-8") as f:
                f.write("Sorter\n")
                f.write(f"Version: {APP_VERSION}\n")
                f.write(f"Build date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"File: {final_name}\n")
                f.write(f"Size: {final_path.stat().st_size} bytes\n")

            print(f"📄 Создан файл информации: {info_file.name}")

            if input("\n📂 Открыть папку Releases? (y/n): ").lower() == "y":
                os.startfile(str(releases_dir))

        else:
            print("❌ Ошибка: EXE файл не найден после сборки!")

    except Exception as e:
        print(f"❌ Ошибка при сборке: {e}")


def create_bat_file():
    """Создаёт build.bat для удобного запуска сборки."""
    content = (
        "@echo off\n"
        "echo Запуск сборки Sorter...\n"
        "python build.py\n"
        "pause\n"
    )

    with open("build.bat", "w", encoding="utf-8") as f:
        f.write(content)

    print("🟢 Создан build.bat")


if __name__ == "__main__":
    create_bat_file()
    build_exe()
