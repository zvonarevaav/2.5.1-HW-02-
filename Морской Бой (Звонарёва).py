import random

class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if not isinstance(other, Dot):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"Dot({self.x}, {self.y})"

class BoardException(Exception):
    pass

class BoardOutException(BoardException):
    def __str__(self):
        return "Вы пытаетесь выстрелить за пределы игрового поля!"

class AlreadyShotException(BoardException):
    def __str__(self):
        return "Вы уже стреляли в эту точку!"

class ShipPlacementException(BoardException):
    def __str__(self):
        return "Невозможно разместить корабль в заданном месте"

class Board:
    def __init__(self, hid=False, size=6):
        self.size = size
        self.hid = hid
        self.field = [["O"] * size for _ in range(size)]
        self.busy = []
        self.ships = []

    def add_ship(self, ship):
        for dot in ship.dots:
            if self.out(dot) or dot in self.busy:
                raise ShipPlacementException()
        for dot in ship.dots:
            self.field[dot.x][dot.y] = "■"
            self.busy.append(dot)
        self.ships.append(ship)
        self.contour(ship)

    def contour(self, ship, verb=False):
        near = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dot in ship.dots:
            for dx, dy in near:
                cur = Dot(dot.x + dx, dot.y + dy)
                if not self.out(cur) and cur not in self.busy:
                    self.busy.append(cur)
                    if verb:
                        self.field[cur.x][cur.y] = "."

    def out(self, dot):
        return not (0 <= dot.x < self.size and 0 <= dot.y < self.size)

    def shot(self, dot):
        if self.out(dot):
            raise BoardOutException()
        if dot in self.busy:
            raise AlreadyShotException()
        self.busy.append(dot)
        for ship in self.ships:
            if dot in ship.dots:
                ship.lives -= 1
                self.field[dot.x][dot.y] = "X"
                if ship.lives == 0:
                    self.contour(ship, verb=True)
                    self.ships.remove(ship)
                    print("Корабль уничтожен!")
                    return True
                else:
                    print("Корабль ранен!")
                    return True
        self.field[dot.x][dot.y] = "T"
        print("Мимо!")
        return False

    def clear_busy(self):
        self.busy = []

    def __str__(self):
        res = "  | " + " | ".join(str(i+1) for i in range(self.size)) + " |\n"
        for i, row in enumerate(self.field):
            res += f"{i+1} | " + " | ".join(row) + " |\n"
        if self.hid:
            res = res.replace("■", "O")
        return res

    def count_ships(self):
        return len([ship for ship in self.ships if ship.lives > 0])

class Ship:
    def __init__(self, bow, length, direction):
        self.bow = bow
        self.length = length
        self.direction = direction
        self.lives = length

    @property
    def dots(self):
        ship_dots = []
        for i in range(self.length):
            cur_x, cur_y = self.bow.x, self.bow.y
            if self.direction == 0:
                cur_x += i
            else:
                cur_y += i
            ship_dots.append(Dot(cur_x, cur_y))
        return ship_dots

class Player:
    def __init__(self, board, enemy_board):
        self.board = board
        self.enemy_board = enemy_board

    def ask(self):
        raise NotImplementedError()

    def move(self):
        while True:
            try:
                target = self.ask()
                repeat = self.enemy_board.shot(target)
                return repeat
            except BoardException as e:
                print(e)

class User(Player):
    def ask(self):
        while True:
            try:
                coords = input("Ваш ход (формат: x y, например 3 5): ").split()
                if len(coords) != 2 or not all(coord.isdigit() for coord in coords):
                    raise ValueError("Некорректный формат ввода.")
                x, y = map(int, coords)
                if not (1 <= x <= self.board.size and 1 <= y <= self.board.size):
                    raise ValueError("Координаты выходят за пределы игрового поля.")
                return Dot(x - 1, y - 1)
            except ValueError as e:
                print(e)

class AI(Player):
    def ask(self):
        x = random.randint(0, self.board.size - 1)
        y = random.randint(0, self.board.size - 1)
        print(f"Ход компьютера: {x+1} {y+1}")
        return Dot(x, y)

class Game:
    def __init__(self, size=6):
        self.size = size
        self.user_board = self.random_board()
        self.ai_board = self.random_board(True)
        self.ai = AI(self.ai_board, self.user_board)
        self.user = User(self.user_board, self.ai_board)

    def random_board(self, hid=False):
        board = Board(hid=hid, size=self.size)
        ship_sizes = [3, 2, 2, 1, 1, 1, 1]
        attempts = 0
        for size in ship_sizes:
            placed = False
            while not placed and attempts < 2000:
                ship = Ship(Dot(random.randint(0, self.size - 1), random.randint(0, self.size - 1)),
                            size, random.randint(0, 1))
                try:
                    board.add_ship(ship)
                    placed = True
                except ShipPlacementException:
                    attempts += 1
            if not placed:
                print("Не удалось разместить все корабли. Попробуйте снова.")
                return None  # Используем None для обозначения неудачной попытки генерации доски
        board.clear_busy()  # Очищаем список занятых точек после размещения кораблей
        return board

    def greet(self):
        print("Добро пожаловать в игру 'Морской бой'!")
        print("Формат ввода: x y (x - номер строки, y - номер столбца)")

    def loop(self):
        num = 0
        while True:
            print("Доска пользователя:")
            print(self.user.board)
            print("\nДоска ИИ:")
            print(self.ai.board)
            if num % 2 == 0:
                print("\nХодит игрок")
                repeat = self.user.move()
            else:
                print("\nХодит ИИ")
                repeat = self.ai.move()
            if not repeat:
                num += 1

            if self.ai.board.count_ships() == 0:
                print("\nПользователь выиграл!")
                break
            if self.user.board.count_ships() == 0:
                print("\nИИ выиграл!")
                break

    def start(self):
        if self.user_board is None or self.ai_board is None:
            print("Ошибка при создании досок. Перезапустите игру.")
            return
        self.greet()
        self.loop()

if __name__ == "__main__":
    g = Game()
    g.start()
