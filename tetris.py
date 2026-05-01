import pygame
import random
import sys

# --- Constants ---
BOARD_COLS = 10
BOARD_ROWS = 20
CELL_SIZE = 32
SIDEBAR_W = 180
WINDOW_W = BOARD_COLS * CELL_SIZE + SIDEBAR_W
WINDOW_H = BOARD_ROWS * CELL_SIZE
FPS = 60
FALL_INTERVAL = 500  # ms between automatic drops (constant, no acceleration)
LOCK_DELAY = 500     # ms before resting piece locks

# --- Colors ---
BLACK      = (10,  10,  10)
DARK_GRAY  = (40,  40,  40)
GRID_COLOR = (60,  60,  60)
WHITE      = (230, 230, 230)
PANEL_BG   = (20,  20,  20)

PIECE_COLORS = {
    'I': (0,   240, 240),
    'O': (240, 240, 0),
    'T': (160, 0,   240),
    'S': (0,   240, 0),
    'Z': (240, 0,   0),
    'J': (0,   0,   240),
    'L': (240, 160, 0),
}

# --- Shape data: 4 rotation states per piece as (dr, dc) offsets ---
SHAPES = {
    'I': [
        [(0,0),(0,1),(0,2),(0,3)],
        [(0,2),(1,2),(2,2),(3,2)],
        [(1,0),(1,1),(1,2),(1,3)],
        [(0,1),(1,1),(2,1),(3,1)],
    ],
    'O': [
        [(0,0),(0,1),(1,0),(1,1)],
        [(0,0),(0,1),(1,0),(1,1)],
        [(0,0),(0,1),(1,0),(1,1)],
        [(0,0),(0,1),(1,0),(1,1)],
    ],
    'T': [
        [(0,1),(1,0),(1,1),(1,2)],
        [(0,1),(1,1),(1,2),(2,1)],
        [(1,0),(1,1),(1,2),(2,1)],
        [(0,1),(1,0),(1,1),(2,1)],
    ],
    'S': [
        [(0,1),(0,2),(1,0),(1,1)],
        [(0,1),(1,1),(1,2),(2,2)],
        [(1,1),(1,2),(2,0),(2,1)],
        [(0,0),(1,0),(1,1),(2,1)],
    ],
    'Z': [
        [(0,0),(0,1),(1,1),(1,2)],
        [(0,2),(1,1),(1,2),(2,1)],
        [(1,0),(1,1),(2,1),(2,2)],
        [(0,1),(1,0),(1,1),(2,0)],
    ],
    'J': [
        [(0,0),(1,0),(1,1),(1,2)],
        [(0,1),(0,2),(1,1),(2,1)],
        [(1,0),(1,1),(1,2),(2,2)],
        [(0,1),(1,1),(2,0),(2,1)],
    ],
    'L': [
        [(0,2),(1,0),(1,1),(1,2)],
        [(0,1),(1,1),(2,1),(2,2)],
        [(1,0),(1,1),(1,2),(2,0)],
        [(0,0),(0,1),(1,1),(2,1)],
    ],
}


class Tetromino:
    def __init__(self, shape_key, row=0, col=3):
        self.shape_key = shape_key
        self.rotation = 0
        self.row = row
        self.col = col

    def cells(self):
        return [(self.row + dr, self.col + dc)
                for dr, dc in SHAPES[self.shape_key][self.rotation]]

    def cells_at(self, row, col, rotation):
        rot = rotation % 4
        return [(row + dr, col + dc)
                for dr, dc in SHAPES[self.shape_key][rot]]

    def color(self):
        return PIECE_COLORS[self.shape_key]

    def move(self, dr, dc):
        self.row += dr
        self.col += dc

    def rotate(self, direction=1):
        self.rotation = (self.rotation + direction) % 4

    @classmethod
    def spawn(cls):
        key = random.choice(list(SHAPES.keys()))
        return cls(key, row=0, col=3)


class Board:
    def __init__(self):
        self.grid = [[None] * BOARD_COLS for _ in range(BOARD_ROWS)]
        self.score = 0
        self.lines_cleared = 0

    def is_valid(self, cells):
        for r, c in cells:
            if r < 0 or r >= BOARD_ROWS or c < 0 or c >= BOARD_COLS:
                return False
            if self.grid[r][c] is not None:
                return False
        return True

    def lock(self, piece):
        for r, c in piece.cells():
            if 0 <= r < BOARD_ROWS and 0 <= c < BOARD_COLS:
                self.grid[r][c] = piece.color()

    def clear_lines(self):
        full_rows = [r for r in range(BOARD_ROWS)
                     if all(self.grid[r][c] is not None for c in range(BOARD_COLS))]
        for r in full_rows:
            del self.grid[r]
            self.grid.insert(0, [None] * BOARD_COLS)
        return len(full_rows)

    def update_score(self, lines):
        points = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}
        self.score += points.get(lines, 800)
        self.lines_cleared += lines

    def is_blocked(self, piece):
        spawn_cells = piece.cells_at(0, 3, 0)
        return not self.is_valid(spawn_cells)

    def reset(self):
        self.grid = [[None] * BOARD_COLS for _ in range(BOARD_ROWS)]
        self.score = 0
        self.lines_cleared = 0


class Game:
    def __init__(self):
        self.board = Board()
        self.current_piece = Tetromino.spawn()
        self.next_piece = Tetromino.spawn()
        self.state = 'playing'
        self.fall_timer = 0
        self.lock_timer = 0
        self.lock_resets = 0
        self.max_lock_resets = 15

    def _on_ground(self):
        cells_below = [(r + 1, c) for r, c in self.current_piece.cells()]
        return not self.board.is_valid(cells_below)

    def new_piece(self):
        self.current_piece = self.next_piece
        self.next_piece = Tetromino.spawn()
        self.fall_timer = 0
        self.lock_timer = 0
        self.lock_resets = 0
        if not self.board.is_valid(self.current_piece.cells()):
            self.state = 'game_over'

    def try_move(self, dr, dc):
        new_cells = [(r + dr, c + dc) for r, c in self.current_piece.cells()]
        if self.board.is_valid(new_cells):
            self.current_piece.move(dr, dc)
            if self.lock_resets < self.max_lock_resets:
                self.lock_timer = 0
                self.lock_resets += 1
            return True
        return False

    def try_rotate(self, direction=1):
        p = self.current_piece
        new_rot = (p.rotation + direction) % 4
        kicks = [(0, 0), (0, -1), (0, 1), (0, -2), (0, 2)]
        for dr, dc in kicks:
            cells = p.cells_at(p.row + dr, p.col + dc, new_rot)
            if self.board.is_valid(cells):
                p.row += dr
                p.col += dc
                p.rotation = new_rot
                if self.lock_resets < self.max_lock_resets:
                    self.lock_timer = 0
                    self.lock_resets += 1
                return True
        return False

    def hard_drop(self):
        dropped = 0
        while self.try_move(1, 0):
            dropped += 1
        self.board.score += dropped * 2
        self.lock_piece()

    def lock_piece(self):
        self.board.lock(self.current_piece)
        lines = self.board.clear_lines()
        self.board.update_score(lines)
        self.new_piece()

    def update(self, dt):
        if self.state != 'playing':
            return
        on_ground = self._on_ground()
        if not on_ground:
            self.lock_timer = 0
            self.fall_timer += dt
            if self.fall_timer >= FALL_INTERVAL:
                self.fall_timer = 0
                self.try_move(1, 0)
        else:
            self.lock_timer += dt
            if self.lock_timer >= LOCK_DELAY:
                self.lock_piece()

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.state == 'game_over':
            if event.key == pygame.K_r:
                self.board.reset()
                self.current_piece = Tetromino.spawn()
                self.next_piece = Tetromino.spawn()
                self.state = 'playing'
                self.fall_timer = 0
                self.lock_timer = 0
            return
        if event.key in (pygame.K_p, pygame.K_ESCAPE):
            self.state = 'paused' if self.state == 'playing' else 'playing'
            return
        if self.state == 'paused':
            return
        if event.key == pygame.K_LEFT:
            self.try_move(0, -1)
        elif event.key == pygame.K_RIGHT:
            self.try_move(0, 1)
        elif event.key == pygame.K_DOWN:
            if self.try_move(1, 0):
                self.board.score += 1
        elif event.key == pygame.K_UP:
            self.try_rotate(1)
        elif event.key == pygame.K_z:
            self.try_rotate(-1)
        elif event.key == pygame.K_SPACE:
            self.hard_drop()


# --- Renderer ---

def draw_cell(surface, row, col, color, offset_x=0, offset_y=0):
    x = offset_x + col * CELL_SIZE
    y = offset_y + row * CELL_SIZE
    pygame.draw.rect(surface, color, (x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2))
    light = tuple(min(255, v + 60) for v in color)
    pygame.draw.rect(surface, light, (x + 1, y + 1, CELL_SIZE - 2, 3))
    pygame.draw.rect(surface, light, (x + 1, y + 1, 3, CELL_SIZE - 2))


def draw_board(surface, board):
    for r in range(BOARD_ROWS):
        for c in range(BOARD_COLS):
            pygame.draw.rect(surface, DARK_GRAY,
                             (c * CELL_SIZE + 1, r * CELL_SIZE + 1,
                              CELL_SIZE - 2, CELL_SIZE - 2))
            if board.grid[r][c] is not None:
                draw_cell(surface, r, c, board.grid[r][c])
    for r in range(BOARD_ROWS + 1):
        pygame.draw.line(surface, GRID_COLOR, (0, r * CELL_SIZE),
                         (BOARD_COLS * CELL_SIZE, r * CELL_SIZE))
    for c in range(BOARD_COLS + 1):
        pygame.draw.line(surface, GRID_COLOR, (c * CELL_SIZE, 0),
                         (c * CELL_SIZE, BOARD_ROWS * CELL_SIZE))


def draw_piece(surface, piece):
    for r, c in piece.cells():
        if r >= 0:
            draw_cell(surface, r, c, piece.color())


def draw_ghost(surface, board, piece):
    ghost_row = piece.row
    while True:
        next_cells = [(ghost_row + 1 + dr, piece.col + dc)
                      for dr, dc in SHAPES[piece.shape_key][piece.rotation]]
        if not board.is_valid(next_cells):
            break
        ghost_row += 1
    ghost_color = tuple(max(0, v - 160) for v in piece.color())
    ghost_color = tuple(min(255, v + 30) for v in ghost_color)
    for dr, dc in SHAPES[piece.shape_key][piece.rotation]:
        r = ghost_row + dr
        c = piece.col + dc
        if r >= 0:
            x = c * CELL_SIZE + 1
            y = r * CELL_SIZE + 1
            pygame.draw.rect(surface, ghost_color,
                             (x, y, CELL_SIZE - 2, CELL_SIZE - 2), 2)


def draw_sidebar(surface, next_piece, score, lines, font_large, font_small):
    sx = BOARD_COLS * CELL_SIZE
    pygame.draw.rect(surface, PANEL_BG, (sx, 0, SIDEBAR_W, WINDOW_H))

    # Next piece
    label = font_small.render("NEXT", True, WHITE)
    surface.blit(label, (sx + 20, 16))
    preview_x = sx + 20
    preview_y = 44
    for dr, dc in SHAPES[next_piece.shape_key][0]:
        px = preview_x + dc * (CELL_SIZE - 4)
        py = preview_y + dr * (CELL_SIZE - 4)
        pygame.draw.rect(surface, next_piece.color(),
                         (px + 1, py + 1, CELL_SIZE - 6, CELL_SIZE - 6))

    # Score
    label = font_small.render("SCORE", True, WHITE)
    surface.blit(label, (sx + 20, 180))
    val = font_large.render(str(score), True, WHITE)
    surface.blit(val, (sx + 20, 200))

    # Lines
    label = font_small.render("LINES", True, WHITE)
    surface.blit(label, (sx + 20, 260))
    val = font_large.render(str(lines), True, WHITE)
    surface.blit(val, (sx + 20, 280))

    # Controls
    controls = [
        ("←→", "Mover"),
        ("↑", "Girar"),
        ("↓", "Descer"),
        ("Z", "Anti-horário"),
        ("SPC", "Drop"),
        ("P", "Pausar"),
    ]
    y = 370
    for key, desc in controls:
        k = font_small.render(key, True, (180, 180, 180))
        d = font_small.render(desc, True, (120, 120, 120))
        surface.blit(k, (sx + 12, y))
        surface.blit(d, (sx + 50, y))
        y += 22


def draw_overlay(surface, lines, font_title, font_sub):
    overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surface.blit(overlay, (0, 0))
    total_h = len(lines) * 44
    start_y = (WINDOW_H - total_h) // 2
    for i, (text, font, color) in enumerate(lines):
        rendered = font.render(text, True, color)
        rx = (WINDOW_W - rendered.get_width()) // 2
        surface.blit(rendered, (rx, start_y + i * 44))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()

    font_large = pygame.font.SysFont("monospace", 26, bold=True)
    font_small = pygame.font.SysFont("monospace", 16)
    font_title = pygame.font.SysFont("monospace", 38, bold=True)
    font_sub   = pygame.font.SysFont("monospace", 20)

    game = Game()

    running = True
    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)

        game.update(dt)

        screen.fill(BLACK)
        draw_board(screen, game.board)
        if game.state in ('playing', 'paused'):
            draw_ghost(screen, game.board, game.current_piece)
            draw_piece(screen, game.current_piece)
        draw_sidebar(screen, game.next_piece, game.board.score,
                     game.board.lines_cleared, font_large, font_small)

        if game.state == 'paused':
            draw_overlay(screen, [
                ("PAUSADO", font_title, WHITE),
                ("P para continuar", font_sub, (180, 180, 180)),
            ], font_title, font_sub)
        elif game.state == 'game_over':
            draw_overlay(screen, [
                ("GAME OVER", font_title, (240, 60, 60)),
                (f"Pontos: {game.board.score}", font_large, WHITE),
                ("R para reiniciar", font_sub, (180, 180, 180)),
            ], font_title, font_sub)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
