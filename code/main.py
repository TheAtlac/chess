"""Интерфейс шахмат и подключение к базе данных"""

import csv
import sqlite3
import sys
from random import choice

from games_table import GamesWidget
from persons_table import PersonWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from chess import BLACK, WHITE, Board, King, Pawn


class Chess(QMainWindow):
    """Класс приложения с игрой "шахматы"."""

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        "Инициализация переменных и расстановка кнопок"
        self.setWindowTitle("Шахматы")
        self.btns = {}
        self.central_widget = QWidget(self)
        self.board = Board()
        self.setCentralWidget(self.central_widget)
        self.vbox = QVBoxLayout(self.central_widget)
        self.grid = QGridLayout(self)  # Здесь будет шахматное поле
        # Имена игроков будут отображаться
        self.person1 = QLabel(self)
        self.person2 = QLabel(self)
        self.vbox.addLayout(self.grid)
        self.persons_box = QHBoxLayout(self)
        self.vbox.addLayout(self.persons_box)
        self.persons_box.addWidget(self.person1)
        self.persons_box.addWidget(self.person2)
        self.selected = False
        self.reboot_btn = QPushButton("перезапустить", self)  # Кнопка перезапуска
        self.reboot_btn.clicked.connect(self.forced_reboot)
        self.vbox.addWidget(self.reboot_btn)
        self.set_field()  # Создаёт поле
        self.reset_field()  # обновляет поле
        self.change = QPushButton("сменить игрока", self)  # Кнопка смены игроков
        self.change.clicked.connect(self.change_player)
        self.vbox.addWidget(self.change)
        self.hbox = QHBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.p_table = QPushButton(
            "просмотреть игроков", self
        )  # Кнопка отображения таблицы
        # игроков
        self.p_table.clicked.connect(self.show_persons_table)
        self.hbox.addWidget(self.p_table)
        self.g_table = QPushButton(
            "просмотреть игры", self
        )  # Кнопка отображения таблицы игр
        self.g_table.clicked.connect(self.show_games_table)
        self.hbox.addWidget(self.g_table)
        self.can_cast = False  # изначально ракировка невозможна

    def reboot(self):
        """Перезапуск поля"""
        self.board = Board()  # Доска создаётся новая
        self.reset_field()  # Иконки обновляются
        # Данные БД сохраняются
        self.con.commit()
        self.cur = self.con.cursor()
        self.file.close()  # Запись ходов окончена
        file = open(f"games/game{self.new_id}.csv", "r")
        cur_game_table = csv.reader(
            file, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        if list(cur_game_table) != ["-"]:  # Если ни одного хода не сделано,
            # то сохранять игру незачем
            print("сохранена игра №", self.new_id)
            self.new_id = (
                max(
                    self.cur.execute("""select id from games""").fetchall(),
                    key=lambda x: x[0],
                )[0]
                + 1
            )
            self.cur.execute(
                """insert into games(id, steps, person1, person2, winner)
                values(?, ?, ?, ?, ?)""",
                (self.new_id, f"game{self.new_id}.csv", self.name1, self.name2, -1),
            )
        self.file = open(f"games/game{self.new_id}.csv", "w")
        self.cur_game_table = csv.writer(
            self.file, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        self.cur_step = 1

    def forced_reboot(self):
        answer, ok_pressed = QInputDialog.getItem(
            self,
            "",
            "Какой исход указать в статистике",
            ("Белые сдались", "Чёрные сдались", "Ничья", "Пометить как неоконченную"),
            0,
            False,
        )
        # Если перезапуск сделан человеком, то об этом должно быть указано
        if ok_pressed:
            if answer == "Пометить как неоконченную":
                self.file.write("-")
                self.cur.execute(
                    f"""UPDATE games SET\n winner=-1\nwhere id={self.new_id}"""
                )
            elif answer == "Ничья":
                self.file.write("=")
                self.cur.execute(
                    f"""UPDATE games SET\n winner=0\nwhere id={self.new_id}"""
                )
            elif answer == "Чёрные сдались":
                self.file.write("#")
                self.cur.execute(
                    f"""UPDATE games SET\n winner=?\nwhere id={self.new_id}""",
                    (self.name1,),
                )
            else:
                self.file.write("#")
                self.cur.execute(
                    f"""UPDATE games SET\n winner=?\nwhere id={self.new_id}""",
                    (self.name2,),
                )
            self.reboot()

    def players_setting(self, color=0):
        """Замена текущих игроков"""
        ok_pressed = False
        if color == 0:
            # Поменяет обоих игроков
            answer = QMessageBox.question(
                self,
                "",
                "Выбрать стороны случайным образом?",
                QMessageBox.Yes,
                QMessageBox.No,
            )
            if answer == QMessageBox.Yes:
                while not ok_pressed:
                    self.name1, ok_pressed = QInputDialog.getItem(
                        self, "", "Впишите имя первого игрока", (), 1, False
                    )
                ok_pressed = False
                while not ok_pressed:
                    self.name2, ok_pressed = QInputDialog.getItem(
                        self, "", "Впишите имя второго игрока", (), 1, False
                    )
                if self.name1 != choice([self.name1, self.name2]):
                    self.name1, self.name2 = self.name2, self.name1
            else:
                while not ok_pressed:
                    self.name1, ok_pressed = QInputDialog.getItem(
                        self, "", "Впишите имя игрока белыми", (), 1, False
                    )
                ok_pressed = False
                while not ok_pressed:
                    self.name2, ok_pressed = QInputDialog.getItem(
                        self, "", "Впишите имя игрока чёрными", (), 1, False
                    )
        else:
            # Поменяет одного (выбранного игрока)
            if color == WHITE:
                while not ok_pressed:
                    self.name1, ok_pressed = QInputDialog.getItem(
                        self, "", "Впишите нового имя игрока белыми", (), 1, False
                    )
                self.name2 = str(
                    self.cur.execute(
                        "select name from persons where id=?", (self.name2,)
                    ).fetchone()[0]
                )
            else:
                while not ok_pressed:
                    self.name2, ok_pressed = QInputDialog.getItem(
                        self, "", "Впишите нового имя игрока чёрными", (), 1, False
                    )
                self.name1 = str(
                    self.cur.execute(
                        "select name from persons where id=?", (self.name1,)
                    ).fetchone()[0]
                )
        # Обновляет информацию о текущих игроках
        self.person1.setText("Белыми: " + str(self.name1))
        self.person2.setText("Чёрными: " + str(self.name2))
        for name in [self.name1, self.name2]:
            # Добавляет игроков в БД (если раньше его там не было)
            if name.isdigit():
                name = int(name)
            if name not in map(
                lambda x: x[0],
                self.cur.execute(
                    """select name from
            persons"""
                ).fetchall(),
            ):
                max_person_id = (
                    max(
                        self.cur.execute(
                            """select id from persons
                """
                        ).fetchall(),
                        key=lambda x: x[0],
                    )[0]
                    + 1
                )
                self.cur.execute(
                    """insert into persons(id, name) values(?, ?)
                """,
                    (max_person_id, name),
                )
        # Заменит имена игроков на их id
        self.name1 = self.cur.execute(
            """select id from persons where name = ?""", (self.name1,)
        ).fetchone()[0]
        self.name2 = self.cur.execute(
            """select id from persons where name = ?""", (self.name2,)
        ).fetchone()[0]

    def change_player(self):
        """Выбрать игроков которых нужно поменять"""
        answer, ok_pressed = QInputDialog.getItem(
            self,
            "",
            "Какого игрока поменять?",
            ("Белыми", "Чёрными", "Обоих", "Поменять местами текущих"),
            0,
            False,
        )
        if ok_pressed:
            if answer == "Обоих":
                self.players_setting()
            elif answer == "Поменять местами текущих":
                # Меняет игроков местами
                self.name1, self.name2 = self.name2, self.name1
                # Обновляет информацию о текущих игроках
                self.person1.setText("Белыми: " + str(self.name1))
                self.person2.setText("Чёрными: " + str(self.name2))
            else:
                if answer == "Белыми":
                    self.players_setting(color=WHITE)
                else:
                    self.players_setting(color=BLACK)
            self.forced_reboot()

    def show_persons_table(self):
        """Создать и отобразит таблицу игроков"""
        self.window2 = PersonWidget(self.cur)
        self.window2.show()

    def show_games_table(self):
        """Создать и отобразит таблицу игр"""
        self.window2 = GamesWidget(self.cur)
        self.window2.show()

    def set_field(self):
        """Создать пустую доску и подключиться к БД"""
        self.con = sqlite3.connect("code/chess_db.sqlite")  # Подключиться к БД
        self.cur = self.con.cursor()
        self.new_id = (
            max(
                self.cur.execute("""select id from games""").fetchall(),
                key=lambda x: x[0],
            )[0]
            + 1
        )  # Максимальный id игр + 1 - id новой игры
        self.file = open(
            f"code/games/game{self.new_id}.csv", "x"
        )  # Будет записывать ходы в csv файл
        self.cur_game_table = csv.writer(
            self.file, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        self.cur_step = 1
        answer = QMessageBox.question(
            self,
            "",
            "Выбрать стороны случайным образом?",
            QMessageBox.Yes,
            QMessageBox.No,
        )
        ok_pressed = False
        if answer == QMessageBox.Yes:  # Выбор сторон случайным образом
            # Определим имена/псевдонимы игроков
            while not ok_pressed:
                self.name1, ok_pressed = QInputDialog.getItem(
                    self, "", "Впишите имя первого игрока", (), 1, False
                )
            ok_pressed = False
            while not ok_pressed:
                self.name2, ok_pressed = QInputDialog.getItem(
                    self, "", "Впишите имя второго игрока", (), 1, False
                )
            if self.name1 != choice([self.name1, self.name2]):
                self.name1, self.name2 = self.name2, self.name1
        else:
            # Определим имена/псевдонимы игроков с выбором сторон
            while not ok_pressed:
                self.name1, ok_pressed = QInputDialog.getItem(
                    self, "", "Впишите имя игрока белыми", (), 1, False
                )
            ok_pressed = False
            while not ok_pressed:
                self.name2, ok_pressed = QInputDialog.getItem(
                    self, "", "Впишите имя игрока чёрными", (), 1, False
                )
        # Обновляет информацию о текущих игроках
        self.person1.setText("Белыми: " + str(self.name1))
        self.person2.setText("Чёрными: " + str(self.name2))
        for name in [self.name1, self.name2]:
            # Добавляет игроков в БД (если раньше его там не было)
            if name.isdigit():
                name = int(
                    name
                )  # SQL сохраняет строки из одних цифр как числа, поэтому сразу
                # приведём их к этому формату (иначе имена из цифр будут сохраняться как новые и
                # статистика будет обнуляться
            if name not in map(
                lambda x: x[0],
                self.cur.execute(
                    """select name from
            persons"""
                ).fetchall(),
            ):
                max_person_id = (
                    max(
                        self.cur.execute(
                            """select id from persons
                """
                        ).fetchall(),
                        key=lambda x: x[0],
                    )[0]
                    + 1
                )
                self.cur.execute(
                    """insert into persons(id, name) values(?, ?)
                """,
                    (max_person_id, name),
                )
        # Заменит имена игроков на их id
        self.name1 = self.cur.execute(
            """select id from persons where name = ?""", (self.name1,)
        ).fetchone()[0]
        self.name2 = self.cur.execute(
            """select id from persons where name = ?""", (self.name2,)
        ).fetchone()[0]
        # Добавит в БД новую игру
        self.cur.execute(
            """insert into games(id, steps, person1, person2, winner)
        values(?, ?, ?, ?, ?)""",
            (self.new_id, f"game{self.new_id}.csv", self.name1, self.name2, -1),
        )
        # Расставит надписи с координатами и кнопки, на которых будут распологаться фигуры
        for i in range(1, 9):
            self.grid.addWidget(QLabel(self), 0, i)
            self.grid.itemAtPosition(0, i).widget().setText(chr(64 + i))
            self.grid.itemAtPosition(0, i).widget().resize(75, 75)
            self.grid.itemAtPosition(0, i).widget().setAlignment(Qt.AlignCenter)
        for row in range(1, 9):
            self.grid.addWidget(QLabel(self), row, 0)
            self.grid.itemAtPosition(row, 0).widget().setText(str(9 - row))
            self.grid.itemAtPosition(row, 0).widget().setAlignment(Qt.AlignCenter)
            self.grid.itemAtPosition(row, 0).widget().resize(75, 75)
            for col in range(1, 9):
                self.grid.addWidget(QPushButton(self), row, col)
                self.grid.itemAtPosition(row, col).widget().resize(75, 75)
                self.grid.itemAtPosition(row, col).widget().clicked.connect(self.click)
                self.grid.itemAtPosition(row, col).widget().setCheckable(True)
                self.btns[self.grid.itemAtPosition(row, col).widget()] = (
                    8 - row,
                    col - 1,
                )
            self.grid.addWidget(QLabel(self), row, 9)
            self.grid.itemAtPosition(row, 9).widget().setText(str(9 - row))
            self.grid.itemAtPosition(row, 9).widget().resize(75, 75)
            self.grid.itemAtPosition(row, 9).widget().setAlignment(Qt.AlignCenter)
        for i in range(1, 9):
            self.grid.addWidget(QLabel(self), 9, i)
            self.grid.itemAtPosition(9, i).widget().setText(chr(64 + i))
            self.grid.itemAtPosition(9, i).widget().resize(75, 75)
            self.grid.itemAtPosition(9, i).widget().setAlignment(Qt.AlignCenter)

    def reset_field(self):
        """Обновление поля"""
        self.selected = False
        result = self.board.check()
        if result:  # Если игра закончена, то пользователь будет уведомлен о результате,
            # поле обновлено, а в БД занесён победитель
            if result == -1:
                QMessageBox.question(self, "", "Ничья", QMessageBox.Yes)
                self.cur_game_table.writerow([self.cur_step, "="])
                self.cur.execute(
                    f"""UPDATE games SET\n winner=0\nwhere id={self.new_id}"""
                )
            else:
                if result == WHITE:
                    winner = "Белые"
                    self.cur.execute(
                        f"""UPDATE games SET\n winner = {self.name1}
where id={self.new_id}"""
                    )
                else:
                    winner = "Чёрные"
                    self.cur.execute(
                        f"""UPDATE games SET\n winner = {self.name2}
where id={self.new_id}"""
                    )
                self.cur_game_table.writerow([self.cur_step, "#"])
                QMessageBox.question(self, "", f"Победили {winner}", QMessageBox.Yes)
            self.reboot()
            return
        for row in range(1, 9):
            for col in range(1, 9):
                if (
                    self.not_none_piece(8 - row, col - 1)
                    and self.board.get_piece(8 - row, col - 1).get_color()
                    != self.board.current_player_color()
                ):
                    self.grid.itemAtPosition(row, col).widget().setEnabled(
                        False
                    )  # Фигуры,
                    # которыми нельзя сходить блокируются
                else:  # Пустые клетки и "свои" фигура разблокируются
                    self.grid.itemAtPosition(row, col).widget().setEnabled(True)
                # Для каждой фигуры устанавливаются иконки
                cell = self.board.cell(8 - row, col - 1)
                self.grid.itemAtPosition(row, col).widget().setChecked(False)
                if cell:
                    self.grid.itemAtPosition(row, col).widget().setIcon(
                        QIcon("сhess_icons/" + cell + ".png")
                    )

    def can_step(self, row, col):
        """Отобразит возможные для выбранной фигуры ходы"""
        piece = self.board.get_piece(row, col)
        # Кнопки с позициями, на которые можно сходить станут нажаты
        if isinstance(
            piece, Pawn
        ):  # Пешка ходит и бьёт по-разному, поэтому прописана отдельна
            for row1, col1 in piece.censor(
                self.board, row, col, piece.can_move(self.board, row, col)
            ):
                self.grid.itemAtPosition(8 - row1, col1 + 1).widget().setChecked(True)
                self.grid.itemAtPosition(8 - row1, col1 + 1).widget().setEnabled(True)
            for row1, col1 in piece.censor(
                self.board, row, col, piece.can_attack(self.board, row, col)
            ):
                self.grid.itemAtPosition(8 - row1, col1 + 1).widget().setChecked(True)
                self.grid.itemAtPosition(8 - row1, col1 + 1).widget().setEnabled(True)
        else:

            for row1, col1 in piece.censor(
                self.board, row, col, piece.can_move(self.board, row, col)
            ):
                self.grid.itemAtPosition(8 - row1, col1 + 1).widget().setChecked(True)
                self.grid.itemAtPosition(8 - row1, col1 + 1).widget().setEnabled(True)

    def not_none_piece(self, row, col):
        """Проверяет, является ли клетка фигурой"""
        return self.board.get_piece(row, col) is not None

    def click(self):
        """Какая-то из кнопок поля нажата - нужно определить что именно делать"""
        if self.selected:
            if self.sender() == self.selected:
                # Сходить без изменения кординаты нельзя - поле просто обновится
                self.reset_field()
                return
            if self.sender().isChecked():
                # Если кнопка до этого не была нажата, то can_step уже определило, что сходить
                # сюда нельзя
                self.reset_field()
            else:
                # Определим координаты клеток для данного хода
                row, col = self.btns[self.selected]
                row1, col1 = self.btns[self.sender()]
                piece = self.board.get_piece(row, col)
                if self.not_none_piece(row1, col1):
                    sign = "x"  # Если что-то будет срублено, то это будет записано а списке ходов
                else:
                    sign = "-"  # Если ход мирный, то это будет записано а списке ходов
                if isinstance(piece, King):
                    if abs(col - col1) == 2:  # Если король ходит на две клетки,
                        # то это точно ракировка
                        if col1 == 2:  # Длинная рокировка
                            self.board.castling0()
                            # Запись длинной ракировки
                            self.cur_game_table.writerow([self.cur_step, "0-0-0"])
                        elif col1 == 6:  # Короткая рокировка
                            self.board.castling7()
                            # Запись короткой ракировки
                            self.cur_game_table.writerow([self.cur_step, "0-0"])
                    else:  # Обычный ход
                        self.board.move_piece(row, col, row1, col1)
                        self.cur_game_table.writerow(
                            [
                                self.cur_step,
                                chr(65 + col)
                                + str(row)
                                + sign
                                + chr(65 + col1)
                                + str(row1),
                            ]
                        )
                elif isinstance(piece, Pawn):
                    if (
                        row1 == piece.end_row()
                    ):  # Если ряд последний, то пешка превращается
                        char, ok_pressed = QInputDialog.getItem(
                            self, "", "выберите фигуру", ("R", "N", "B", "Q"), 1, False
                        )
                        if ok_pressed:
                            self.board.move_and_promote_pawn(row, col, row1, col1, char)
                            self.cur_game_table.writerow(
                                [
                                    self.cur_step,
                                    chr(65 + col)
                                    + str(row)
                                    + sign
                                    + chr(65 + col1)
                                    + str(row1),
                                    char,
                                ]
                            )
                    else:
                        self.board.move_piece(row, col, row1, col1)
                        if (
                            row == row1
                        ):  # Если ряд не меняется, то это взятие на проходе
                            if piece.get_color() == WHITE:
                                row1 += 1
                            else:
                                row1 -= 1
                        # В csv файле ход будет записан с действительным номером ряда
                        self.cur_game_table.writerow(
                            [
                                self.cur_step,
                                chr(65 + col)
                                + str(row)
                                + sign
                                + chr(65 + col1)
                                + str(row1),
                            ]
                        )
                else:  # Обычный ход
                    self.board.move_piece(row, col, row1, col1)
                    self.cur_game_table.writerow(
                        [
                            self.cur_step,
                            chr(65 + col)
                            + str(row)
                            + sign
                            + chr(65 + col1)
                            + str(row1),
                        ]
                    )
                self.cur_step += 1  # Счётсчик номера хода увеличивается каждый ход
                self.reset_field()  # Все клетки в конце хода обновляются
                self.selected = False
            return

        if self.not_none_piece(*self.btns[self.sender()]):
            # Если клетка только выбрана, то это отображается
            self.sender().setChecked(True)
            # Также отображаются клетки, куда можно пойти
            self.can_step(*self.btns[self.sender()])
            # Теперь последней выбранной считается только что нажатая кнопка
            self.selected = self.sender()


def main():
    """Запуск игры и отображение"""
    app = QApplication(sys.argv)
    ex = Chess()
    ex.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
