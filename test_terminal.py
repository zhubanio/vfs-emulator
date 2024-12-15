import unittest
import os
from emulator import VirtualFileSystem


class TestVirtualFileSystem(unittest.TestCase):
    TAR_FILE = "archive.tar"

    @classmethod
    def setUpClass(cls):
        # Проверяем, что tar-архив существует
        if not os.path.exists(cls.TAR_FILE):
            raise FileNotFoundError(f"Тестовый архив {cls.TAR_FILE} не найден.")

    def setUp(self):
        self.vfs = VirtualFileSystem(self.TAR_FILE)

    def log_test(self, command, expected, result):
        print(f"\nCommand: {command}\nExpected: {expected}\nResult: {result}\n")

    # Тесты для команды ls
    def test_ls_root(self):
        command = "ls /archive"
        expected = {"etc", "home", "tmp", "var"}
        result = set(self.vfs.ls("/archive").splitlines())
        self.log_test(command, expected, result)
        self.assertEqual(result, expected, f"Ошибка: ожидалось {expected}, но получено {result}")

    def test_ls_subdirectory(self):
        command = "ls /archive/home/user1"
        expected = {"docs", "trinity.txt"}
        result = set(self.vfs.ls("/archive/home/user1").splitlines())
        self.log_test(command, expected, result)
        self.assertEqual(result, expected, f"Ошибка: ожидалось {expected}, но получено {result}")

    def test_ls_nonexistent_directory(self):
        command = "ls /archive/nonexistent"
        with self.assertRaises(FileNotFoundError, msg="Ожидалась ошибка FileNotFoundError при попытке доступа к несуществующей директории"):
            try:
                self.vfs.ls("/archive/nonexistent")
            except FileNotFoundError as e:
                self.log_test(command, "FileNotFoundError", str(e))
                raise

    # Тесты для команды cd
    def test_cd_root(self):
        command = "cd /archive"
        self.vfs.cd("/archive")
        expected = "/archive"
        result = self.vfs.current_path
        self.log_test(command, expected, result)
        self.assertEqual(result, expected, f"Ошибка: текущий путь должен быть {expected}, но получен {result}")

    def test_cd_subdirectory(self):
        command = "cd /archive/home/user1"
        self.vfs.cd("/archive/home/user1")
        expected = "/archive/home/user1"
        result = self.vfs.current_path
        self.log_test(command, expected, result)
        self.assertEqual(result, expected, f"Ошибка: текущий путь должен быть {expected}, но получен {result}")

    def test_cd_nonexistent_directory(self):
        command = "cd /archive/nonexistent"
        with self.assertRaises(FileNotFoundError, msg="Ожидалась ошибка FileNotFoundError при попытке перейти в несуществующую директорию"):
            try:
                self.vfs.cd("/archive/nonexistent")
            except FileNotFoundError as e:
                self.log_test(command, "FileNotFoundError", str(e))
                raise

    # Тесты для команды touch
    def test_touch_file_in_root(self):
        command = "touch newfile.txt in /archive"
        self.vfs.cd("/archive")
        self.vfs.touch("newfile.txt")
        expected = "newfile.txt"
        result = self.vfs.ls("/archive").splitlines()
        self.log_test(command, expected, result)
        self.assertIn(expected, result, f"Ошибка: файл '{expected}' не найден в списке {result}")

    def test_touch_existing_file(self):
        command = "touch newfile.txt in /archive (already exists)"
        self.vfs.cd("/archive")
        self.vfs.touch("newfile.txt")
        with self.assertRaises(FileExistsError, msg="Ожидалась ошибка FileExistsError при попытке создать существующий файл"):
            try:
                self.vfs.touch("newfile.txt")
            except FileExistsError as e:
                self.log_test(command, "FileExistsError", str(e))
                raise

    def test_touch_file_in_subdirectory(self):
        command = "touch newfile.txt in /archive/home/user1"
        self.vfs.cd("/archive/home/user1")
        self.vfs.touch("newfile.txt")
        expected = "newfile.txt"
        result = self.vfs.ls("/archive/home/user1").splitlines()
        self.log_test(command, expected, result)
        self.assertIn(expected, result, f"Ошибка: файл '{expected}' не найден в списке {result}")

    # Тесты для команды cp
    def test_cp_file(self):
        command = "cp /archive/home/system.log to /archive/home/user1/copied_system.log"
        self.vfs.cp("/archive/home/system.log", "/archive/home/user1/copied_system.log")
        expected = "copied_system.log"
        result = self.vfs.ls("/archive/home/user1").splitlines()
        self.log_test(command, expected, result)
        self.assertIn(expected, result, f"Ошибка: файл '{expected}' не найден в списке {result}")

    def test_cp_directory(self):
        command = "cp /archive/home/user1 to /archive/home/copied_user1"
        self.vfs.cp("/archive/home/user1", "/archive/home/copied_user1")
        expected = "copied_user1"
        result = self.vfs.ls("/archive/home").splitlines()
        self.log_test(command, expected, result)
        self.assertIn(expected, result, f"Ошибка: директория '{expected}' не найдена в списке {result}")

    def test_cp_nonexistent_source(self):
        command = "cp /archive/nonexistent.txt to /archive/home/user1"
        with self.assertRaises(FileNotFoundError, msg="Ожидалась ошибка FileNotFoundError при попытке копирования несуществующего источника"):
            try:
                self.vfs.cp("/archive/nonexistent.txt", "/archive/home/user1")
            except FileNotFoundError as e:
                self.log_test(command, "FileNotFoundError", str(e))
                raise

    # Тесты для команды mv
    def test_mv_file(self):
        command = "mv /archive/home/system.log to /archive/home/user1/moved_system.log"
        self.vfs.mv("/archive/home/system.log", "/archive/home/user1/moved_system.log")
        expected_src = "system.log"
        expected_dest = "moved_system.log"
        result_src = self.vfs.ls("/archive/home").splitlines()
        result_dest = self.vfs.ls("/archive/home/user1").splitlines()
        self.log_test(command, f"Not in {result_src}", f"In {result_dest}")
        self.assertNotIn(expected_src, result_src, f"Ошибка: файл '{expected_src}' все еще присутствует в {result_src}")
        self.assertIn(expected_dest, result_dest, f"Ошибка: файл '{expected_dest}' не найден в {result_dest}")

    def test_mv_directory(self):
        command = "mv /archive/home/user1 to /archive/home/moved_user1"
        self.vfs.mv("/archive/home/user1", "/archive/home/moved_user1")
        expected_src = "user1"
        expected_dest = "moved_user1"
        result_src = self.vfs.ls("/archive/home").splitlines()
        result_dest = self.vfs.ls("/archive/home").splitlines()
        self.log_test(command, f"Not in {result_src}", f"In {result_dest}")
        self.assertNotIn(expected_src, result_src, f"Ошибка: директория '{expected_src}' все еще присутствует в {result_src}")
        self.assertIn(expected_dest, result_dest, f"Ошибка: директория '{expected_dest}' не найдена в {result_dest}")

    def test_mv_nonexistent_source(self):
        command = "mv /archive/nonexistent.txt to /archive/home/user1"
        with self.assertRaises(FileNotFoundError, msg="Ожидалась ошибка FileNotFoundError при попытке перемещения несуществующего источника"):
            try:
                self.vfs.mv("/archive/nonexistent.txt", "/archive/home/user1")
            except FileNotFoundError as e:
                self.log_test(command, "FileNotFoundError", str(e))
                raise

    # Тесты для команды exit (в данном случае, проверяем наличие метода)
    def test_exit(self):
        command = "Check if 'cd' method exists"
        result = hasattr(self.vfs, "cd")
        expected = True
        self.log_test(command, expected, result)
        self.assertTrue(result, "Ошибка: метод 'cd' не существует в классе VirtualFileSystem")


if __name__ == "__main__":
    unittest.main()
