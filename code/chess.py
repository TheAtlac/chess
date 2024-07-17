""" классы шахматной доски и фигур"""

from itertools import permutations, product
from copy import deepcopy

WHITE = 1
BLACK = 2


def opponent(color):
    """Возвращает противоположный цвет"""
    if color == WHITE:
        return BLACK
    return WHITE


def correct_coords(row, col):
    """Проверяет, что координаты лежат внутри доски"""
    return 0 <= row < 8 and 0 <= col < 8


class Board:
    """Класс шахматной доски доски"""

    def __init__(self):
        self.color = WHITE
        self.field = []
        # Переменная для хранения информации о том, что пешка сделала ход в две клетки
        # для реализации взятие на проходе
        self.d_p = False
        # Заполняет доску фигурами
        for row in range(8):
            self.field.append([None] * 8)
        self.field[0] = [
            Rook(WHITE), Knight(WHITE), Bishop(WHITE), Queen(WHITE),
            King(WHITE), Bishop(WHITE), Knight(WHITE), Rook(WHITE)
        ]
        self.field[1] = [
            Pawn(WHITE), Pawn(WHITE), Pawn(WHITE), Pawn(WHITE),
            Pawn(WHITE), Pawn(WHITE), Pawn(WHITE), Pawn(WHITE)
        ]
        self.field[6] = [
            Pawn(BLACK), Pawn(BLACK), Pawn(BLACK), Pawn(BLACK),
            Pawn(BLACK), Pawn(BLACK), Pawn(BLACK), Pawn(BLACK)
        ]
        self.field[7] = [
            Rook(BLACK), Knight(BLACK), Bishop(BLACK), Queen(BLACK),
            King(BLACK), Bishop(BLACK), Knight(BLACK), Rook(BLACK)
        ]
        # Переменные для быстрого обращения к координатам короля для проверки невозможных ходов
        self.w_king = self.field[0][4]
        self.b_king = self.field[7][4]
        # Словарь со всеми фигурами для быстрой проверки на мат и невозможные ходы
        self.figures = {BLACK: {}, WHITE: {}}
        for row in range(6, 8):
            for col in range(8):
                self.figures[BLACK][self.field[row][col]] = (row, col)
        for row in range(2):
            for col in range(8):
                self.figures[WHITE][self.field[row][col]] = (row, col)
        # Переменная для информации о фигурах, до "безопасного хода"
        self.save = [(None,), (None,)]

    def check(self):
        """Проверка на мат или ничью"""
        for figure in self.figures[self.color].keys():
            # Для пеешки дополнительно нужно проверять возможсть срубить, т.к. У неё ход и атака
            # различаются
            if isinstance(figure, Pawn):
                if figure.censor(self, *self.figures[self.color][figure],
                                 figure.can_move(self, *self.figures[self.color][figure])) or \
                        figure.censor(self, *self.figures[self.color][figure],
                                      figure.can_attack(self, *self.figures[self.color][figure])):
                    return False
            else:
                if figure.censor(self, *self.figures[self.color][figure],
                                 figure.can_move(self, *self.figures[self.color][figure])):
                    return False
        # Если ни одна фигура не может сходить, значит игра окончена
        king_coords = self.figures[self.color][self.get_king(self.color)]
        # Если король при этом под атакой, значит выиграл цвет, противоположный текущему
        for figure in self.figures[opponent(self.color)].keys():
            if king_coords in figure.censor(self, *self.figures[opponent(self.color)][figure],
                                            figure.can_attack(self,
                                                              *self.figures[opponent(self.color)]
                                                              [figure])):
                return opponent(self.color)
        # Иначе ничья
        return -1

    def current_player_color(self):
        """Возвращает цвет текущего игрока"""
        return self.color

    def get_king(self, color):
        """Возвращает короля нужного цвета"""
        if color == WHITE:
            return self.w_king
        return self.b_king

    def cell(self, row, col):
        """Возвращает строку из двух символов. Если в клетке (row, col)
        находится фигура, символы цвета и фигуры. Если клетка пуста,
        то два пробела"""
        piece = self.field[row][col]
        if piece is None:
            return '  '
        color = piece.get_color()
        color = 'w' if color == WHITE else 'b'
        return color + piece.char()

    def get_piece(self, row, col):
        """Возвращает фигуру на нужной позиции"""
        if correct_coords(row, col):
            return self.field[row][col]
        return None

    def doule_pawn(self):
        """Возвращает возможность взятия на проходе"""
        return self.d_p

    def move_piece(self, row, col, row1, col1):
        """Делает ход"""
        # Взятие на проходе только сразу после хода пешки в две клетки
        self.d_p = False
        piece = self.field[row][col]
        if isinstance(piece, Pawn):
            # Информация о двойном ходе пешке сохраняется
            if abs(row - row1) == 2:
                self.d_p = (row1, col1)
            # Совершение взятия на проходе
            elif row == row1:
                del self.figures[opponent(self.color)][self.field[row1][col1]]
                self.field[row1][col1] = None
                if self.color == WHITE:
                    row1 += 1
                else:
                    row1 -= 1
        piece.move()
        self.field[row][col] = None  # Снять фигуру.
        if self.field[row1][col1] is not None:
            # Убрать срубленную фигуру
            del self.figures[opponent(piece.color)][self.field[row1][col1]]
        self.field[row1][col1] = piece  # Поставить на новое место.
        self.figures[self.color][piece] = (row1, col1)  # Обновить информацию о позиции фигуры
        self.color = opponent(self.color)  # Цвет игрока меняется после хода

    def safe_move(self, row, col, row1, col1):
        """"Совершение "безопасного хода" - проверки на возможности фигуры после такого хода и
        наличия шаха королю после такого хода (После этого хода фигуры будут возвращены на
        старые места"""
        piece = self.field[row][col]
        # Информация о задействованых фигурах - потом они будут возвращены
        self.save = [((row, col), piece), ((row1, col1), self.field[row1][col1])]
        self.field[row][col] = None
        if self.field[row1][col1] is not None:
            del self.figures[opponent(piece.get_color())][self.field[row1][col1]]
        self.field[row1][col1] = piece  # Поставить на новое место.
        self.figures[piece.get_color()][piece] = (row1, col1)

    def load(self):
        """Возвращает фигуры после "безопасного хода"."""
        piece1, piece2 = self.save
        (row1, col1), piece1 = piece1
        (row2, col2), piece2 = piece2
        self.field[row1][col1] = piece1
        self.field[row2][col2] = piece2
        self.figures[piece1.get_color()][piece1] = (row1, col1)
        if piece2 is not None:
            self.figures[piece2.get_color()][piece2] = (row2, col2)

    def move_and_promote_pawn(self, row, col, row1, col1, char):
        """При достижении последнего ряда пешка превращается"""
        piece = self.get_piece(row, col)
        self.field[row][col] = None
        del self.figures[self.color][piece]
        if char == 'R':
            piece = Rook(self.color)
        elif char == 'N':
            piece = Knight(self.color)
        elif char == 'B':
            piece = Bishop(self.color)
        elif char == 'Q':
            piece = Queen(self.color)
        self.figures[self.color][piece] = (row1, col1)
        if self.field[row1][col1]:
            del self.figures[opponent(self.color)][self.field[row1][col1]]
        self.field[row1][col1] = piece
        self.color = opponent(self.color)
        return True

    def can_castling0(self):
        """Проверка возможности сделать ракировку к 1-му ряду"""
        if self.color == WHITE:
            piece1, piece2 = self.get_piece(0, 0), self.get_piece(0, 4)
        else:
            piece1, piece2 = self.get_piece(7, 0), self.get_piece(7, 4)
        if not (isinstance(piece1, Rook) and isinstance(piece2, King)):
            return False
        # Если фгуры ходили, то ракировка невозможна
        if not (piece1.not_moved() and piece2.not_moved()):
            return False
        if self.color == WHITE:
            # Через шах нельзя делать ракировку
            for figure in self.figures[opponent(self.color)].keys():
                if (0, 2) in figure.can_attack(self, *self.figures[opponent(self.color)][figure]) \
                        or (0, 3) in figure.can_attack(self, *self.figures[opponent(self.color)]
                [figure]) or (0, 4) in figure.can_attack(self, *self.figures[opponent(self.color)]
                [figure]):
                    return False
            if (0, 3) in piece1.can_move(self, 0, 0):
                return True
            return False
        # Через шах нельзя делать ракировку
        for figure in self.figures[opponent(self.color)].keys():
            if (7, 2) in figure.can_attack(self, *self.figures[opponent(self.color)][figure]) \
                    or (7, 3) in figure.can_attack(self, *self.figures[opponent(self.color)]
            [figure]) or (7, 4) in figure.can_attack(self, *self.figures[opponent(self.color)]
            [figure]):
                return False
        if (7, 3) in piece1.can_move(self, 7, 0):
            return True
        return False

    def castling0(self):
        """Совершение ракировки(после проверки на её возможность"""
        if self.color == WHITE:
            piece2 = self.get_piece(0, 4)
        else:
            piece2 = self.get_piece(7, 4)
        if self.color == WHITE:
            self.figures[self.color][self.field[0][4]] = (0, 2)
            self.move_piece(0, 0, 0, 3)
            self.field[0][4] = None
            self.figures[self.color][piece2] = (0, 2)
            piece2.move()
            self.field[0][2] = piece2
        else:
            self.figures[self.color][self.field[7][4]] = (7, 2)
            self.move_piece(7, 0, 7, 3)
            self.field[7][4] = None
            self.figures[self.color][piece2] = (7, 2)
            self.field[7][2] = piece2

    def can_castling7(self):
        """Проверка возможности сделать ракировку к 8-му ряду"""
        if self.color == WHITE:
            piece1, piece2 = self.get_piece(0, 7), self.get_piece(0, 4)
        else:
            piece1, piece2 = self.get_piece(7, 7), self.get_piece(7, 4)
        if not (isinstance(piece1, Rook) and isinstance(piece2, King)):
            return False
        # Если фгуры ходили, то ракировка невозможна
        if not (piece1.not_moved() and piece2.not_moved()):
            return False
        if self.color == WHITE:
            # Через шах нельзя делать ракировку
            for figure in self.figures[opponent(self.color)].keys():
                if (0, 4) in figure.can_attack(self, *self.figures[opponent(self.color)][figure]) \
                        or (0, 5) in figure.can_attack(self, *self.figures[opponent(self.color)]
                [figure]) or (0, 6) in figure.can_attack(self, *self.figures[opponent(self.color)]
                [figure]):
                    return False
            if (0, 5) in piece1.can_move(self, 0, 7):
                return True
            return False
        # Через шах нельзя делать ракировку
        for figure in self.figures[opponent(self.color)].keys():
            if (7, 4) in figure.can_attack(self, *self.figures[opponent(self.color)][figure]) \
                    or (7, 5) in \
                    figure.can_attack(self, *self.figures[opponent(self.color)][figure]) or \
                    (7, 6) in figure.can_attack(self,
                                                *self.figures[opponent(self.color)][figure]):
                return False
        if (7, 5) in piece1.can_move(self, 7, 7):
            return True
        return False

    def castling7(self):
        """Совершение ракировки(после проверки на её возможность"""
        if self.color == WHITE:
            piece2 = self.get_piece(0, 4)
        else:
            piece2 = self.get_piece(7, 4)
        if self.color == WHITE:
            self.figures[self.color][self.field[0][4]] = (0, 6)
            self.move_piece(0, 7, 0, 5)
            self.field[0][4] = None
            piece2.move()
            self.field[0][6] = piece2
        else:
            self.figures[self.color][self.field[7][4]] = (7, 6)
            self.move_piece(7, 7, 7, 5)
            self.field[7][4] = None
            piece2.move()
            self.field[7][6] = piece2


class Figure:
    """Базовый класс фигуры"""

    def __init__(self, color):
        self.color = color
        self.no_move = True

    def get_color(self):
        """Возвращает цвет фигуры"""
        return self.color

    def char(self):
        """Возвращает букву фигуры"""
        return 'F'

    def not_moved(self):
        """Возвращает информацию о том, ходила ли фигура"""
        return self.no_move

    def move(self):
        """Сохраняет информацию о том что фигура уже ходила"""
        self.no_move = False

    def __repr__(self):
        """Возвращает буквы цвета и фигуры для наглядности во время отладки"""
        if self.color == WHITE:
            return 'w' + self.char()
        return 'b' + self.char()

    def censor(self, board, row, col, moves):
        """Проверяет что ход возможен"""
        king = board.get_king(board.get_piece(row, col).get_color())
        king_coords = board.figures[king.get_color()][king]
        cur_op_color = opponent(self.color)
        for row1, col1 in deepcopy(moves):
            if isinstance(board.get_piece(row, col), King):
                king_coords = row1, col1
            if board.get_piece(row1, col1):
                if board.get_piece(row, col).get_color() == \
                        board.get_piece(row1, col1).get_color():
                    moves.remove((row1, col1))
                    continue
            # Делает безопасный ход
            board.safe_move(row, col, row1, col1)
            # Если король окажется под атакой, то такой ход невозможен
            for figure in board.figures[cur_op_color].keys():
                if king_coords in figure.can_attack(board, *board.figures[cur_op_color][figure]):
                    moves.remove((row1, col1))
                    break
            # Возвращает фигуры на старые места
            board.load()
        # Вернёт только те, которые прошли проверку
        return moves


class Rook(Figure):
    """Ладья"""

    def char(self):
        """R - Rook"""
        return 'R'

    def can_move(self, board, row, col):
        """Возможные ходы"""
        out = []
        # Ладья ходит только по горизонтали и вертикали, не проходит сквозь фигуры
        for row1 in range(row + 1, 8):
            if board.get_piece(row1, col) is not None:
                out.append((row1, col))
                break
            out.append((row1, col))
        for row1 in range(row - 1, -1, -1):
            if board.get_piece(row1, col) is not None:
                out.append((row1, col))
                break
            out.append((row1, col))
        for col1 in range(col + 1, 8):
            if board.get_piece(row, col1) is not None:
                out.append((row, col1))
                break
            out.append((row, col1))
        for col1 in range(col - 1, -1, -1):
            if board.get_piece(row, col1) is not None:
                out.append((row, col1))
                break
            out.append((row, col1))
        return out

    def can_attack(self, board, row, col):
        """Бьёт ладья так же, как и ходит"""
        return self.can_move(board, row, col)


class Pawn(Figure):
    """Пешка"""

    def end_row(self):
        """Последний ряд - для превращения пешки"""
        if self.color == BLACK:
            return 0
        return 7

    def char(self):
        """P - pawn"""
        return 'P'

    def can_move(self, board, row, col):
        """Возможные ходы"""
        out = []
        # Пешка ходит только в одном направлении (в зависимости от цвета)
        if self.color == WHITE:
            direction = 1
        else:
            direction = -1
        # Она не срубает обычным ходом
        if board.get_piece(row + direction, col) is None:
            out.append((row + direction, col))
            # Не ходит сквозь
            if self.no_move and board.get_piece(row + direction * 2, col) is None:
                out.append((row + direction * 2, col))
        return out

    def can_attack(self, board, row, col):
        """Возможные атаки"""
        out = []
        # Пешка бьёт только в одном направлении (в зависимости от цвета)
        if self.color == WHITE:
            direction = 1
        else:
            direction = -1
        # Бьёт только по диагонали
        if board.get_piece(row + direction, col + 1) is not None:
            out.append((row + direction, col + 1))
        if board.get_piece(row + direction, col - 1) is not None:
            out.append((row + direction, col - 1))
        d_p = board.doule_pawn()
        if d_p:
            # Взятие на проходе после двойного хода
            if d_p[0] == row and (d_p[1] == col + 1 or d_p[1] == col - 1):
                out.append(d_p)
        return out


class King(Figure):
    """Король"""

    def char(self):
        """K - King"""
        return 'K'

    def can_move(self, board, row, col):
        """Возможные ходы"""
        out = []

        cur_op_color = opponent(self.color)
        for i, j in product([-1, 0, 1], repeat=2):
            if i == j == 0:
                continue
            if not correct_coords(row + i, col + j):
                continue
            flag = True
            # Нельзя ходить под шах
            for figure in board.figures[cur_op_color]:
                if (row + i, col + j) in figure.can_attack(board,
                                                           *board.figures[cur_op_color][figure]):
                    flag = False
                    break
            if flag:
                out.append((row + i, col + j))
        if self.color == WHITE:
            row1 = 0
        else:
            row1 = 7
        # Если ракировка возможна только начиная с короля
        if board.can_castling0():
            out.append((row1, 2))
        if board.can_castling7():
            out.append((row1, 6))
        return out

    def can_attack(self, board, row, col):
        """Если атака короля будет аналогичной ходу, то начнётся бесконечная рекурсия"""
        out = []
        for i, j in product([-1, 0, 1], repeat=2):
            if i == j == 0:
                continue
            if not correct_coords(row + i, col + j):
                continue
            out.append((row + i, col + j))
        return out


class Knight(Figure):
    """Конь"""

    def char(self):
        """kNight, буква 'K' уже занята королём"""
        return 'N'

    def can_move(self, board, row, col):
        """Возможные ходы"""
        out = []
        for i, j in permutations([-2, -1, 1, 2], 2):
            if abs(i) + abs(j) == 3 and correct_coords(row + i, col + j):
                out.append((row + i, col + j))
        return out

    def can_attack(self, board, row, col):
        """Возможные атаки (аналогичны обычному ходу)"""
        return self.can_move(board, row, col)


class Bishop(Figure):
    """Слон"""

    def char(self):
        """Bishop - B"""
        return 'B'

    def can_move(self, board, row, col):
        """Возможные ходы"""
        out = []
        for i in range(1, min(7 - row, 7 - col) + 1):
            if not correct_coords(row + i, col + i):
                break
            if board.get_piece(row + i, col + i) is not None:
                out.append((row + i, col + i))
                break
            out.append((row + i, col + i))
        for i in range(1, min(7 - row, col) + 1):
            if not correct_coords(row + i, col - i):
                break
            if board.get_piece(row + i, col - i) is not None:
                out.append((row + i, col - i))
                break
            out.append((row + i, col - i))
        for i in range(1, min(row, 7 - col) + 1):
            if not correct_coords(row - i, col + i):
                break
            if board.get_piece(row - i, col + i) is not None:
                out.append((row - i, col + i))
                break
            out.append((row - i, col + i))
        for i in range(1, min(row, col) + 1):
            if not correct_coords(row - i, col - i):
                break
            if board.get_piece(row - i, col - i) is not None:
                out.append((row - i, col - i))
                break
            out.append((row - i, col - i))
        return out

    def can_attack(self, board, row, col):
        """Возможные атаки (аналогичны обычному ходу)"""
        return self.can_move(board, row, col)


class Queen(Bishop, Rook):
    """Ферзь"""

    def char(self):
        """Queen - Q"""
        return 'Q'

    def can_move(self, board, row, col):
        """Возможные ходы"""
        # Возможные ходы - совокупность ходов ладьи и слона
        return Bishop.can_move(self, board, row, col) + \
               Rook.can_move(self, board, row, col)

    def can_attack(self, board, row, col):
        """Возможные атаки (аналогичны обычному ходу)"""
        return self.can_move(board, row, col)
