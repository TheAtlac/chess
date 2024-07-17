"""Классы таблицы игр и списка ходов"""
import csv
from PyQt5.QtWidgets import QLabel, QPushButton, QTableWidgetItem, QTableWidget, QWidget,\
    QVBoxLayout, QMessageBox

class GameTable(QWidget):
    def __init__(self, steps):
        super().__init__()
        self.steps = steps
        self.initUI()

    def initUI(self):
        self.setGeometry(500, 500, 540, 400)
        name = self.steps.split('.')[0]
        self.setWindowTitle('Список ходов ' + name)
        self.vbox = QVBoxLayout(self)
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.vbox.addWidget(self.table_widget)
        self.set_game()

    def set_game(self):
        """Заполняет таблицу с ходами выбранной игры"""
        with open('games/'+self.steps, 'r', newline='\n', encoding='utf8') as csvfile:
            reader = csv.reader(
                csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                if len(row) > 1:
                    row = row[1]
                    # разниц между мирным ходом и срубанием должна быть заметна
                    if row.count('-') == 1:
                        row = row.split('-')
                        row.insert(1, '-')
                    elif 'x' in row:
                        row = row.split('x')
                        row.insert(1, 'x')
                self.table_widget.setRowCount(self.table_widget.rowCount() + 1)
                for j, val in enumerate(row):
                    self.table_widget.setItem(self.table_widget.rowCount() - 1, j,
                                             QTableWidgetItem(str(val)))


class GamesWidget(QWidget):
    """Виджет визуализирует таблицу со всеми играми, занесёнными в базу данных"""
    def __init__(self, cur):
        super().__init__()
        self.cur = cur
        self.initUI()

    def initUI(self):
        # Инструкция по открытию произвольной игры
        QMessageBox.question(
            self, '', "Для просмотра игры нужно выбрать ячейку или строку с нужной игрой и нажать"
                      " кнопку посмотреть",
            QMessageBox.Yes)
        self.setGeometry(500, 500, 540, 400)
        self.setWindowTitle('Таблица игр')
        self.vbox = QVBoxLayout(self)
        self.table_widget = QTableWidget()
        self.vbox.addWidget(self.table_widget)
        self.set_games()
        self.btn = QPushButton('Просмотреть игру', self)
        self.btn.clicked.connect(self.see_game)
        self.vbox.addWidget(self.btn)
        # Информация об ошибке(изначально скрыта)
        self.error_status = QLabel(self)
        self.vbox.addWidget(self.error_status)
        self.error_status.hide()

    def set_games(self):
        """заполняет таблицу данными"""
        request = "SELECT distinct * FROM games where id>0 and winner!=-1 order by id"
        # берёт информацию обо всех законченных играх
        result = self.cur.execute(request).fetchall()
        self.table_widget.setColumnCount(5)
        self.table_widget.setRowCount(len(result))
        # Устанавливает заголовки колонок
        self.table_widget.setHorizontalHeaderLabels([description[0] for
                                                    description in self.cur.description])
        # Распределяет по тоблице нформацию об играх
        for i, elem in enumerate(result):
            elem = list(elem)
            # Заменит id на понятные имена
            elem[2] = self.cur.execute("select name from persons where id=?", (str(elem[2]), )) \
                .fetchone()[0]
            elem[3] = self.cur.execute("select name from persons where id=?", (str(elem[3]), )) \
                .fetchone()[0]
            elem[4] = self.cur.execute("select name from persons where id=?", (str(elem[4]), )) \
                .fetchone()[0]
            for j, val in enumerate(elem):
                self.table_widget.setItem(i, j,
                                         QTableWidgetItem(str(val)))

    def see_game(self):
        """Просмотр ходов выбранной игры"""

        self.error_status.hide()
        selected = list(self.table_widget.selectedItems())
        if len(selected) > 1:
            self.error_status.show()
            self.error_status.setText('Невозможно загрузить более одной игры')
        elif len(selected) == 0:
            self.error_status.show()
            self.error_status.setText('Не выбрано ни одной игры')
        else:
            selected = selected[0].row()
            steps = self.table_widget.item(selected, 1).text()
            self.game = GameTable(steps)
            self.game.show()
