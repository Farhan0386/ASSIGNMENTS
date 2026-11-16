// Box.asm - Draws a black box while a key is pressed, clears it when released.
// Screen geometry: 32 words per row (16 pixels/word), base address = 16384 (SCREEN).
// Customize these 3 constants for your personal number K:
//   START_OFFSET = (start_row * 32) + start_word_col
//   WIDTH_WORDS  = box width in pixels / 16 (e.g., 2 words = 32 pixels)
//   HEIGHT_ROWS  = box height in rows (e.g., 32 rows)

(MAIN_LOOP)
    @KBD
    D=M
    @SET_BLACK
    D;JNE               // If key pressed (KBD != 0), fill color = -1 (black)

    @color
    M=0                 // Else fill color = 0 (white)
    @DRAW_BOX
    0;JMP

(SET_BLACK)
    @color
    M=-1                // -1 = 16'b1111111111111111 (all 16 pixels black)

(DRAW_BOX)
    // Base address of top-left word of the box: SCREEN + START_OFFSET
    @SCREEN
    D=A
    @1608               // <-- REPLACE with your START_OFFSET (e.g., row 50 * 32 + col 8 = 1608)
    D=D+A
    @row_addr
    M=D

    @32                 // <-- REPLACE with your HEIGHT_ROWS
    D=A
    @rows_left
    M=D

(ROW_LOOP)
    @rows_left
    D=M
    @MAIN_LOOP
    D;JEQ               // Done drawing all rows; poll keyboard again

    @row_addr
    D=M
    @curr_addr
    M=D                 // curr_addr = start of current row

    @2                  // <-- REPLACE with your WIDTH_WORDS (width_in_pixels / 16)
    D=A
    @cols_left
    M=D

(COL_LOOP)
    @cols_left
    D=M
    @NEXT_ROW
    D;JEQ               // Finished columns in this row

    @color
    D=M
    @curr_addr
    A=M
    M=D                 // Memory[curr_addr] = color (-1 or 0)

    @curr_addr
    M=M+1               // Move 16 pixels right (+1 word)
    @cols_left
    M=M-1
    @COL_LOOP
    0;JMP

(NEXT_ROW)
    @32
    D=A
    @row_addr
    M=M+D               // Advance row_addr by 32 words (next scanline down)
    @rows_left
    M=M-1
    @ROW_LOOP
    0;JMP