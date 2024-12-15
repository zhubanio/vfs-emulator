import tkinter as tk
from tkinter import scrolledtext
import argparse
import tarfile
from pathlib import Path


class VirtualFileSystem:
    def __init__(self, tar_path):
        self.filesystem = {}
        self.current_path = "/"
        self.load_tar(tar_path)

    def load_tar(self, tar_path):
        with tarfile.open(tar_path, "r") as tar:
            for member in tar.getmembers():
                parts = Path(member.name).parts
                current = self.filesystem
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                if member.isfile():
                    current[parts[-1]] = None
                else:
                    current[parts[-1]] = {}

    def ls(self, path=None):
        if path is None:
            # Если путь не указан, используем текущую директорию
            current = self._get_current_dir()
        else:
            # Получаем абсолютный путь
            if path == "/":
                target_path = "/"
            elif path == "..":
                target_path = str(Path(self.current_path).parent.as_posix())
            else:
                target_path = (Path(self.current_path) / path).as_posix()

            # Проверяем доступность указанного пути
            current = self.filesystem
            try:
                if target_path == "/":
                    current = self.filesystem
                else:
                    for part in target_path.split("/")[1:]:  # Пропускаем корень "/"
                        # Проверяем, что current — словарь, иначе путь некорректен
                        if not isinstance(current, dict):
                            raise NotADirectoryError(f"{path} is not a directory.")
                        current = current[part]
                    # Проверяем, что конечный объект — это словарь
                    if not isinstance(current, dict):
                        raise NotADirectoryError(f"{path} is not a directory.")
            except KeyError:
                raise FileNotFoundError(f"There is no such directory.")

        # Возвращаем содержимое директории
        return "\n".join(current.keys())

    def _get_current_dir(self):
        # Приводим путь в POSIX-совместимый формат и получаем текущую директорию
        current = self.filesystem
        for part in Path(self.current_path).as_posix().split("/"):
            if part:  # Пропускаем пустые части пути
                current = current[part]
        return current

    def cd(self, path):
        # Реализация перехода по директориям
        if path == "/":
            self.current_path = "/"
        elif path == "..":
            self.current_path = str(Path(self.current_path).parent.as_posix())
        else:
            new_path = (Path(self.current_path) / path).as_posix()
            current = self.filesystem
            try:
                for part in new_path.split("/")[1:]:
                    current = current[part]
                if current is None:
                    raise NotADirectoryError(f"{path} is not a directory.")
                self.current_path = "/" + str(new_path)[1:]
            except KeyError:
                raise FileNotFoundError(f"Directory {path} not found.")

    def cp(self, source, destination):
        # Получаем абсолютные пути
        src_path = (Path(self.current_path) / source).as_posix()
        dest_path = (Path(self.current_path) / destination).as_posix()

        # Обработка специальных случаев для корня и родителя
        if source == "/":
            src_path = "/"
        elif source == "..":
            src_path = str(Path(self.current_path).parent.as_posix())
        if destination == "/":
            dest_path = "/"
        elif destination == "..":
            dest_path = str(Path(self.current_path).parent.as_posix())
        src_parts = src_path.split("/")
        dest_parts = dest_path.split("/")
        # Проверяем, что источник существует
        current = self.filesystem
        try:
            for part in src_parts[1:]:
                current = current[part]
        except KeyError:
            raise FileNotFoundError(f"Source {source} not found.")

        # Проверяем, что источник и цель не совпадают
        if dest_path.startswith(src_path):
            raise ValueError("Cannot copy an object to itself.")

        # Проверяем, что в целевой директории нет объекта с тем же именем
        parent_dest = self.filesystem

        try:
            for part in dest_parts[1:]:  # Переходим к родительской директории
                parent_dest = parent_dest[part]
            if dest_parts[-1] in parent_dest:  # Проверяем последний сегмент пути
                raise FileExistsError(f"Destination already contains an object named {dest_parts[-1]}.")
        except KeyError:
            pass  # Путь назначения пока не существует, можно продолжать.

        # Выполняем копирование
        self._copy_item(src_path.split("/")[1:], dest_path.split("/")[1:])

    def _copy_item(self, src_parts, dest_parts):
        # Рекурсивное копирование файлов и директорий
        current_src = self.filesystem
        current_dest = self.filesystem

        # Переходим к источнику
        for part in src_parts[:-1]:
            current_src = current_src[part]
        item_to_copy = current_src[src_parts[-1]]

        # Переходим к месту назначения
        for part in dest_parts:
            if part:  # Пропускаем пустые части пути
                current_dest = current_dest.setdefault(part, {})

        # Копируем объект
        if isinstance(item_to_copy, dict):  # Если это директория
            current_dest[src_parts[-1]] = {k: v for k, v in item_to_copy.items()}
        else:  # Если это файл
            current_dest[src_parts[-1]] = None

    def touch(self, filename):
        # Создает пустой файл в текущей директории
        current = self._get_current_dir()
        if filename in current:
            raise FileExistsError(f"File '{filename}' already exists.")
        current[filename] = None  # None символизирует пустой файл

       def tree(self, path=None, prefix=""):
        """
        Выводит дерево файлов и папок начиная с указанного пути.
        Если путь не указан, используется текущая директория.
        """
            if path is None:
                path = self.current_path
    
            # Получаем текущую директорию
            current = self.filesystem
            try:
                for part in Path(path).parts[1:]:
                    current = current[part]
            except KeyError:
                raise FileNotFoundError(f"Path {path} not found.")
    
            # Строка для накопления результата
            result = []
    
            # Рекурсивная функция для построения дерева
            def _build_tree(subtree, pref):
                items = list(subtree.keys())
                for i, item in enumerate(items):
                    # Определяем символ для последнего элемента
                    connector = "└── " if i == len(items) - 1 else "├── "
                    result.append(f"{pref}{connector}{item}")
    
                    # Если элемент — директория, рекурсивно выводим её содержимое
                    if isinstance(subtree[item], dict):
                        extension = "    " if i == len(items) - 1 else "│   "
                        _build_tree(subtree[item], pref + extension)
    
            # Построение дерева
            _build_tree(current, prefix)
    
            # Возвращаем результат в виде строки
            return "\n".join(result)

    def mv(self, source, destination):
        # print("self.current_path:")
        # print(self.current_path)

        # Получаем абсолютные пути
        src_path = (Path(self.current_path) / source).as_posix()
        dest_path = (Path(self.current_path) / destination).as_posix()
        if source == "/":
            src_path = "/"
        elif source == "..":
            src_path = str(Path(self.current_path).parent.as_posix())
        if destination == "/":
            dest_path = "/"
        elif destination == "..":
            dest_path = str(Path(self.current_path).parent.as_posix())
        dest_parts = dest_path.split("/")
        if src_path in self.current_path or self.current_path.startswith(src_path):
            raise ValueError("Cannot move a directory that contains the current working directory.")

        # Проверяем, что источник существует
        current = self.filesystem
        # print("current:")
        # print(current)
        try:
            for part in src_path.split("/")[1:]:
                # print("part:")
                # print(part)
                current = current[part]
                # print("current:")
                # print(current)
        except KeyError:
            raise FileNotFoundError(f"Source {source} not found.")

        # Проверяем, что источник и цель не совпадают
        if dest_path.startswith(src_path):
            raise ValueError("Cannot copy an object to itself.")

            # Проверяем, что в целевой директории нет объекта с тем же именем
        parent_dest = self.filesystem

        try:
            for part in dest_parts[1:]:  # Переходим к родительской директории
                parent_dest = parent_dest[part]
            if dest_parts[-1] in parent_dest:  # Проверяем последний сегмент пути
                raise FileExistsError(f"Destination already contains an object named {dest_parts[-1]}.")
        except KeyError:
            pass  # Путь назначения пока не существует, можно продолжать.

        # Перемещаем объект
        self._move_item(src_path.split("/")[1:], dest_path.split("/")[1:])

    def _move_item(self, src_parts, dest_parts):
        # Рекурсивное перемещение файлов и директорий
        current_src = self.filesystem
        current_dest = self.filesystem

        # Переходим к источнику
        for part in src_parts[:-1]:
            current_src = current_src[part]
        item_to_move = current_src.pop(src_parts[-1])  # Удаляем объект из источника

        # Переходим к месту назначения
        for part in dest_parts:
            if part:
                current_dest = current_dest.setdefault(part, {})

        # Перемещаем объект
        current_dest[src_parts[-1]] = item_to_move


class TerminalGUI:
    def __init__(self, user, tar_path):
        self.vfs = VirtualFileSystem(tar_path)
        self.user = user

        # Создание окна GUI
        self.root = tk.Tk()
        self.root.title("Virtual File System Emulator")

        # История терминала
        self.output_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', height=20, width=80)
        self.output_area.grid(row=0, column=0, padx=10, pady=10, columnspan=2)

        # Поле ввода команды
        self.command_entry = tk.Entry(self.root, width=60)
        self.command_entry.grid(row=1, column=0, padx=10, pady=10)
        self.command_entry.bind("<Return>", self.process_command)

        # Кнопка отправки команды
        self.send_button = tk.Button(self.root, text="Send", command=self.process_command)
        self.send_button.grid(row=1, column=1, padx=10, pady=10)

        self.print_output(f"Добро пожаловать, {self.user}!")
        self.print_output(
            "Введите команду. Доступные команды: ls, cd <path>, touch <filename>, cp <source> <destination>, "
            "mv <source> <destination>, exit")
        self.print_output(f"{self.user}@vfs:{self.vfs.current_path}$", end=" ")

    def print_output(self, text, end="\n"):
        """
        Вывод текста в текстовую область эмулятора.
        :param text: Текст для вывода.
        :param end: Окончание строки (по умолчанию "\n").
        """
        self.output_area.configure(state='normal')
        self.output_area.insert(tk.END, text + end)  # Используем заданное окончание строки
        self.output_area.configure(state='disabled')
        self.output_area.see(tk.END)

    def process_command(self, event=None):
        # Your command processing logic here
        pass
        command = self.command_entry.get()
        self.command_entry.delete(0, tk.END)

        if command.strip():
            self.print_output(command)

        try:
            if command.startswith("ls"):
                # Разделить команду на части
                parts = command.split(maxsplit=1)
                if len(parts) == 1:  # Если путь не указан
                    path = None
                else:  # Если путь указан
                    path = parts[1]

                # Выполнить ls с переданным путём
                result = self.vfs.ls(path)
                self.print_output(result)
            elif command.startswith("cd"):
                _, path = command.split(" ", 1)
                self.vfs.cd(path)
            elif command.startswith("touch"):
                _, filename = command.split(" ", 1)
                self.vfs.touch(filename)
            elif command.startswith("cp"):
                _, source, destination = command.split(" ", 2)
                self.vfs.cp(source, destination)
                self.print_output(f"Скопировано: {source} -> {destination}")
            elif command.startswith("mv"):
                _, source, destination = command.split(" ", 2)
                self.vfs.mv(source, destination)
                self.print_output(f"Перемещено: {source} -> {destination}")
            elif command.startswith("tree"):
                result = self.vfs.tree()
                self.print_output(result)
            elif command == "exit":
                self.root.quit()
            else:
                self.print_output(f"Неизвестная команда: {command}")
        except Exception as e:
            self.print_output(f"Ошибка: {str(e)}")

        self.print_output(f"{self.user}@vfs:{self.vfs.current_path}$ ", end="")

    def run(self):
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="Эмулятор виртуальной файловой системы.")
    parser.add_argument('--user', required=True, help="Имя пользователя для отображения в эмуляторе.")
    parser.add_argument('--tar', required=True, help="Путь к tar-архиву виртуальной файловой системы.")
    args = parser.parse_args()
    user = args.user
    gui = TerminalGUI(user=user, tar_path=args.tar)
    gui.run()


if __name__ == "__main__":
    main()
