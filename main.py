import pygame
import sys
import random

pygame.init()

pygame.key.set_repeat(200, 50)

# Window setup
SCREEN_WIDTH = 550
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tetris")
PIECE_SIZE = 32
GRID_WIDTH = 10
GRID_HEIGHT = 20
SCORE = 0

game_over = False
font = pygame.font.SysFont("Arial", 50, bold=True)
hold_font = pygame.font.SysFont("Arial", 20, bold=True)

clock = pygame.time.Clock()
FPS = 60

# PIECES
# Relative block offsets (col_offset, row_offset) and colors for the 7 Tetrominoes
PIECES = {
    'I': {
        'shape': [(0, 0), (-1, 0), (1, 0), (2, 0)],
        'color': (0, 200, 200)  # CYAN
    },
    'O': {
        'shape': [(0, 0), (1, 0), (0, 1), (1, 1)],
        'color': (255, 255, 0)  # YELLOW
    },
    'T': {
        'shape': [(0, 0), (-1, 0), (1, 0), (0, 1)],
        'color': (128, 0, 128)  # PURPLE
    },
    'L': {
        'shape': [(0, -1), (0, 0), (0, 1), (1, 1)],
        'color': (255, 165, 0)  # ORANGE
    },
    'J': {
        'shape': [(0, 0), (0, -1), (0, 1), (-1, 1)],
        'color': (0, 0, 255)    # BLUE
    },
    'S': {
        'shape': [(1, -1), (0, -1), (0, 0), (-1, 0)],
        'color': (0, 255, 0)    # GREEN
    },
    'Z': {
        'shape': [(-1, 1), (0, -1), (0, 0), (-1, 0)],
        'color': (255, 0, 0)    # RED
    }
}

def draw_active_piece(surf, piece_data, anchor_col, anchor_row):
    color = piece_data['color']
    
    for col_offset, row_offset in piece_data['shape']:
        # 1. Find actual cell coordinate on the board
        grid_col = anchor_col + col_offset
        grid_row = anchor_row + row_offset
        
        # 2. Convert grid position to pixel coordinates
        pixel_x = BOARD_X + (grid_col * BLOCK_SIZE)
        pixel_y = BOARD_Y + (grid_row * BLOCK_SIZE)
        
        # 3. Draw the solid block
        pygame.draw.rect(surf, color, (pixel_x, pixel_y, BLOCK_SIZE, BLOCK_SIZE))
        
        # 4. Draw a dark outline so adjacent blocks don't blend into one solid blob
        pygame.draw.rect(surf, (20, 20, 20), (pixel_x, pixel_y, BLOCK_SIZE, BLOCK_SIZE), 1)

# BOARD
BOARD_X = 25
BOARD_Y = 25
BLOCK_SIZE = PIECE_SIZE
board = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

def draw_board(surf, grid):
    # Gridlines
    for row in range(GRID_HEIGHT):
        for col in range(GRID_WIDTH):
            x = BOARD_X + col * BLOCK_SIZE
            y = BOARD_Y + row * BLOCK_SIZE
            
            # Draw individual block if occupied, otherwise outline empty cell
            if grid[row][col]:
                pygame.draw.rect(surf, grid[row][col], (x, y, BLOCK_SIZE, BLOCK_SIZE))
            else:
                pygame.draw.rect(surf, (50, 50, 50), (x, y, BLOCK_SIZE, BLOCK_SIZE), 1)

    # Border
    border_thickness = 4
    board_rect = pygame.Rect(BOARD_X, BOARD_Y, GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE)
    outer_rect = board_rect.inflate(border_thickness * 2, border_thickness * 2)
    pygame.draw.rect(surf, (255, 255, 255), outer_rect, width=border_thickness)

#Falling
FALL_EVENT = pygame.USEREVENT + 1
fall_speed = 500
pygame.time.set_timer(FALL_EVENT, fall_speed)

def is_valid_position(piece_data, anchor_col, anchor_row, grid):
    for col_offset, row_offset in piece_data['shape']:
        target_col = anchor_col + col_offset
        target_row = anchor_row + row_offset

        # Check left and right walls
        if target_col < 0 or target_col >= GRID_WIDTH:
            return False

        # Check floor
        if target_row >= GRID_HEIGHT:
            return False

        # 3. Check collision with locked pieces
        if target_row >= 0 and grid[target_row][target_col] is not None:
            return False

    # If all true
    return True

def lock_piece(piece_data, anchor_col, anchor_row, grid):
    color = piece_data['color']

    for col_offset, row_offset in piece_data['shape']:
        target_col = anchor_col + col_offset
        target_row = anchor_row + row_offset

        # Only store blocks that are inside visible rows
        if target_row >= 0:
            grid[target_row][target_col] = color

def rotate_shape(shape, char):
    if char == 'z':
        # Rotate 90 degrees clockwise
        return [(row, -col) for col, row in shape]
    elif char == 'x':
        # Rotate 90 degrees counter-clockwise   
        return [(-row, col) for col, row in shape]

def clear_full_rows(grid):
    remaining_rows = [row for row in grid if None in row]
    
    # How many rows were cleared
    cleared_count = GRID_HEIGHT - len(remaining_rows)
    
    global SCORE
    if cleared_count == 1:
        SCORE += 100
    elif cleared_count == 2:
        SCORE += 300
    elif cleared_count == 3:
        SCORE += 500
    elif cleared_count == 4:
        SCORE += 800

    # Insert fresh empty rows at the top
    if cleared_count > 0:
        empty_rows = [[None for _ in range(GRID_WIDTH)] for _ in range(cleared_count)]
        # Mutate the grid in-place using slice assignment
        grid[:] = empty_rows + remaining_rows
        
    return cleared_count

#QUEUE
queue = [random.choice(list(PIECES.values())) for _ in range(7)]
QUEUE_X = 412
QUEUE_Y = 100

def draw_next_queue(surf, queue, sidebar_x, sidebar_y):
    MINI_BLOCK_SIZE = 20
    SLOT_SPACING = 80

    # loop through only first 4
    for index, piece in enumerate(queue[:4]):
        # get top anchor position for slot
        slot_x = sidebar_x + 20
        slot_y = sidebar_y + (index * SLOT_SPACING) + 40

        # draw each block of the preview piece
        for col_offset, row_offset in piece['shape']:
            pixel_x = slot_x + (col_offset * MINI_BLOCK_SIZE)
            pixel_y = slot_y + (row_offset * MINI_BLOCK_SIZE)

            # Draw block fill and dark border
            pygame.draw.rect(surf, piece['color'], (pixel_x, pixel_y, MINI_BLOCK_SIZE, MINI_BLOCK_SIZE))
            pygame.draw.rect(surf, (20, 20, 20), (pixel_x, pixel_y, MINI_BLOCK_SIZE, MINI_BLOCK_SIZE), 1)

# HOLD BOX
HOLD_X = 400 
HOLD_Y = 550
def draw_hold_box(surf, held_piece, hold_x, hold_y):
    MINI_BLOCK_SIZE = 20
    BOX_WIDTH = 100
    BOX_HEIGHT = 100

    # Draw panel container border
    pygame.draw.rect(surf, (50, 50, 50), (hold_x, hold_y, BOX_WIDTH, BOX_HEIGHT), 2)

    # If a piece is held, draw its blocks inside the box
    if held_piece is not None:
        # Offset starting position to align piece neatly inside the panel
        center_x = hold_x + 36
        center_y = hold_y + 40

        for col_offset, row_offset in held_piece['shape']:
            pixel_x = center_x + (col_offset * MINI_BLOCK_SIZE)
            pixel_y = center_y + (row_offset * MINI_BLOCK_SIZE)

            # Block fill
            pygame.draw.rect(surf, held_piece['color'], (pixel_x, pixel_y, MINI_BLOCK_SIZE, MINI_BLOCK_SIZE))
            # Dark border outline
            pygame.draw.rect(surf, (20, 20, 20), (pixel_x, pixel_y, MINI_BLOCK_SIZE, MINI_BLOCK_SIZE), 1)

current_piece = queue.pop(0)
current_col = 3
current_row = 0

draw_hold_box(screen, None, HOLD_X, HOLD_Y)
running = True
while running:
    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Triggered automatically every 500ms by Pygame's timer
        elif event.type == FALL_EVENT:
            # Test if moving down 1 row is valid
            if is_valid_position(current_piece, current_col, current_row + 1, board):
                current_row += 1
            else:
                # If moving down is invalid, the piece hit the floor or another piece!
                lock_piece(current_piece, current_col, current_row, board)
                # Check for and clear any completed lines
                lines_cleared = clear_full_rows(board)
                # Spawn new piece at top
                current_piece = queue.pop(0)
                queue.append(random.choice(list(PIECES.values())))
                current_col = 3
                current_row = 0

                if not is_valid_position(current_piece, current_col, current_row, board):
                    game_over = True

        # Handle Key Presses
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z or event.key == pygame.K_x:
                # Create candidate rotated shape
                char = 'z' if event.key == pygame.K_z else 'x'
                rotated_shape = rotate_shape(current_piece['shape'], char)
        
                # Define kick offsets to test in order:
                kick_offsets = [(0, 0), (1, 0), (-1, 0), (0, -1)]
        
                # Create a temporary piece dictionary to test validation
                test_piece = {'shape': rotated_shape, 'color': current_piece['color']}
        
                for col_shift, row_shift in kick_offsets:
                    test_col = current_col + col_shift
                    test_row = current_row + row_shift
            
                # Check if rotated piece fits at the shifted position
                if is_valid_position(test_piece, test_col, test_row, board):
                    # Apply rotation and position shift, then stop checking kicks
                    current_piece['shape'] = rotated_shape
                    current_col = test_col
                    current_row = test_row
                    current_row += 1
                    break
            elif event.key == pygame.K_SPACE:
                draw_hold_box(screen, current_piece, HOLD_X, HOLD_Y)
            elif event.key == pygame.K_UP:
                valid = True
                while valid:
                    if is_valid_position(current_piece, current_col, current_row + 1, board):
                        current_row += 1
                    else:
                        valid = False
                        lock_piece(current_piece, current_col, current_row, board)
            # Move Left
            elif event.key == pygame.K_LEFT:
                if is_valid_position(current_piece, current_col - 1, current_row, board):
                    current_col -= 1

            # Move Right
            elif event.key == pygame.K_RIGHT:
                if is_valid_position(current_piece, current_col + 1, current_row, board):
                    current_col += 1

            # Soft Drop
            elif event.key == pygame.K_DOWN:
                if is_valid_position(current_piece, current_col, current_row + 1, board):
                    current_row += 1
                else:
                    # If soft-dropping into a surface, lock immediately
                    lock_piece(current_piece, current_col, current_row, board)
                    lines_cleared = clear_full_rows(board, SCORE)
                    current_piece = queue.pop(0)
                    queue.append(random.choice(list(PIECES.values())))
                    current_col = 3
                    current_row = 0

                    if not is_valid_position(current_piece, current_col, current_row, board):
                        game_over = True

    # Drawing
    screen.fill((30, 30, 30))

    draw_board(screen, board)
    draw_next_queue(screen, queue, QUEUE_X, QUEUE_Y)
    
    score_text = font.render(str(SCORE), True, (255, 255, 255))
    score_rect = score_text.get_rect(center=(450, 50))
    screen.blit(score_text, score_rect)

    if not game_over:
        draw_active_piece(screen, current_piece, current_col, current_row)
    else:
        # Render Game Over text overlay
        text_surface = font.render("GAME OVER", True, (255, 50, 50))
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(text_surface, text_rect)

    pygame.display.flip()

    clock.tick(FPS)

# Clean exit
pygame.quit()
sys.exit()