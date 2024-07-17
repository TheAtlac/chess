"""Класс с таблицей всех игроков"""
from PyQt5.QtWidgets import QTableWidgetItem, QTableWidget, QWidget, QVBoxLayout


class PersonWidget(QWidget):
    """Виджет визуализирует таблицу со всеми игроками, занесёнными в базу данных"""

    def __init__(self, cur):
        super().__init__()
        self.cur = cur
        self.initUI()

    def initUI(self):
        self.setGeometry(500, 500, 450, 400)
        self.setWindowTitle('Список игроков')
        self.vbox = QVBoxLayout(self)
        self.table_widget = QTableWidget()
        self.vbox.addWidget(self.table_widget)
        self.set_persons()

    def set_persons(self):
        """заполняет таблицу данными"""
        request = "SELECT * FROM persons where id>0"
        # берёт информацию обо всех игроках в базе данных кроме ничьей,
        # которая тоже считается ироком
        result = self.cur.execute(request).fetchall()
        self.table_widget.setColumnCount(4)
        # Устанавливает заголовки колонок
        self.table_widget.setHorizontalHeaderLabels([description[0] for
                                                    description in self.cur.description] + \
                                                   ['процент побед', 'количество игр'])
        # Полученную информацию распределяет по тоблице
        for elem in result:
            games = self.cur.execute(
                "select winner from games where (person1=? or person2=?) "
                "and winner!=-1", (elem[0], elem[0])).fetchall()
            # Если игрок не участвовал ни в одной завершённой игре,
            # то незачем добавлять пустую строку
            if games:
                self.table_widget.setRowCount(self.table_widget.rowCount() + 1)
                for j, val in enumerate(elem):
                    self.table_widget.setItem(self.table_widget.rowCount() - 1, j,
                                             QTableWidgetItem(str(val)))
                    # Для интереса добавим в статистику игрока % его побед и число всех игр
                self.table_widget.setItem(self.table_widget.rowCount() - 1, 2,
                                         QTableWidgetItem(str(round(games.count((elem[0],)) /
                                                                    len(games) * 100, 2)) + '%'))
                self.table_widget.setItem(self.table_widget.rowCount() - 1, 3,
                                         QTableWidgetItem(str(len(games))))
