#!/usr/bin/env python3
"""Test runner and terminal visualizer for the K=178 Box.hack program."""

import os
import sys

STUDENT_NAME = "Priyanshu Kumar"
ROLL_NUMBER = "2501010178"
K = 178
BOX_HEIGHT = 20
BOX_WORDS = (K % 4) + 1
SCREEN_BASE = 16384
SCREEN_WORDS_PER_ROW = 32
BOX_START = SCREEN_BASE + SCREEN_WORDS_PER_ROW * K

def load_rom(hack_file):
    with open(hack_file, "r") as f:
        return [int(line.strip(), 2) for line in f if line.strip()]

def simulate_hack(rom, key_pressed=0, max_cycles=4000, initial_ram=None):
    ram = list(initial_ram) if initial_ram is not None else [0] * 32768
    ram[24576] = key_pressed  # Set Keyboard Memory Map (KBD)

    pc = 0
    a = 0
    d = 0

    for _ in range(max_cycles):
        if pc >= len(rom):
            break
        instr = rom[pc]

        if (instr & 0x8000) == 0:
            # A-instruction
            a = instr
            pc += 1
        else:
            # C-instruction: 111 a cccccc ddd jjj
            a_bit = (instr >> 12) & 1
            comp  = (instr >> 6) & 0x3F
            dest  = (instr >> 3) & 7
            jump  = instr & 7

            y = ram[a] if a_bit else a
            x = d

            zx = (comp >> 5) & 1
            nx = (comp >> 4) & 1
            zy = (comp >> 3) & 1
            ny = (comp >> 2) & 1
            f  = (comp >> 1) & 1
            no = comp & 1

            x_val = 0 if zx else x
            if nx: x_val = (~x_val) & 0xFFFF
            y_val = 0 if zy else y
            if ny: y_val = (~y_val) & 0xFFFF

            out = (x_val + y_val) if f else (x_val & y_val)
            if no: out = (~out) & 0xFFFF
            out &= 0xFFFF

            signed_out = out if out < 0x8000 else out - 0x10000
            zr = 1 if signed_out == 0 else 0
            ng = 1 if signed_out < 0 else 0
            pos = 1 if signed_out > 0 else 0

            if dest & 1: ram[a] = signed_out
            if dest & 2: d = signed_out
            if dest & 4: a = signed_out & 0x7FFF

            do_jump = (jump & 1 and pos) or (jump & 2 and zr) or (jump & 4 and ng)
            if do_jump:
                pc = a
            else:
                pc += 1

    return ram

def main():
    hack_path = "Box.hack"
    if not os.path.exists(hack_path):
        print(f"Error: {hack_path} not found. Run assembler.py Box.asm first.")
        sys.exit(1)

    print("=" * 65)
    print(f"   HACK COMPUTER SIMULATION: Box.hack ({STUDENT_NAME} | {ROLL_NUMBER} | K={K})")
    print("=" * 65)

    rom = load_rom(hack_path)
    print(f"Loaded ROM: {len(rom)} instructions from {hack_path}\n")

    # Step 1: No key pressed
    print("[1] TESTING KEY RELEASED (KBD = 0):")
    ram_white = simulate_hack(rom, key_pressed=0, max_cycles=3000)
    screen_drawn_white = sum(
        1 for r in range(256) for c in range(SCREEN_WORDS_PER_ROW)
        if ram_white[SCREEN_BASE + r * SCREEN_WORDS_PER_ROW + c] != 0
    )
    if screen_drawn_white != 0:
        raise AssertionError(f"Expected a blank screen when no key is pressed, found {screen_drawn_white} non-white words.")
    print(f"    Total black words on screen: {screen_drawn_white}")
    print("    Result: PASS -> Screen is completely clean (white).\n")

    # Step 2: Key pressed ('K', ASCII 75)
    print("[2] TESTING KEY PRESSED (KBD = 75 / 'K'):")
    ram_black = simulate_hack(rom, key_pressed=75, max_cycles=3000)

    rows_drawn = []
    for r in range(256):
        row_words = [ram_black[16384 + r * 32 + c] for c in range(32)]
        cols = [c for c, w in enumerate(row_words) if w != 0]
        if cols:
            rows_drawn.append((r, cols))

    expected_rows = list(range(K, K + BOX_HEIGHT))
    expected_columns = list(range(BOX_WORDS))
    drawn_rows = [row for row, _ in rows_drawn]
    if drawn_rows != expected_rows:
        raise AssertionError(f"Expected rows {expected_rows}, but got {drawn_rows}.")
    for row, columns in rows_drawn:
        if columns != expected_columns:
            raise AssertionError(f"Row {row}: expected black words {expected_columns}, but got {columns}.")
    total_black_words = sum(
        1 for row_offset in range(BOX_HEIGHT) for col in expected_columns
        if ram_black[BOX_START + row_offset * SCREEN_WORDS_PER_ROW + col] == -1
    )
    expected_black_words = BOX_HEIGHT * BOX_WORDS
    if total_black_words != expected_black_words:
        raise AssertionError(f"Expected {expected_black_words} black words, got {total_black_words}.")

    print(f"    Rows with black pixels: {len(rows_drawn)} rows (Expected: {BOX_HEIGHT} rows)")
    if rows_drawn:
        print(f"    First row drawn: Row {rows_drawn[0][0]} (Columns: {rows_drawn[0][1]})")
        print(f"    Last row drawn:  Row {rows_drawn[-1][0]} (Columns: {rows_drawn[-1][1]})")
    print(f"    Total black words: {total_black_words} (Expected: {expected_black_words})")

    print(f"\n[3] VISUAL TERMINAL SCREEN RENDERING (Rows {K - 2} to {K + BOX_HEIGHT + 1}):")
    print("    Col 0 (16px)    Col 1 (16px)    Col 2 (16px)    Col 3 (Rest of screen)")
    print("    " + "-" * 62)

    for r in range(K - 2, K + BOX_HEIGHT + 2):
        words = [ram_black[16384 + r * 32 + c] for c in range(4)]
        line = f"R{r:02d}| "
        for w in words[:3]:
            if w != 0:
                line += "[##############] "
            else:
                line += "[..............] "
        line += "[...blank...] "
        if K <= r < K + BOX_HEIGHT:
            line += f"<-- Box Row {r - K + 1:02d}/{BOX_HEIGHT}"
        print(line)

    # Step 3: Key released again after being pressed
    print("\n[4] TESTING KEY RELEASE TRANSITION (Key released back to 0):")
    ram_cleared = simulate_hack(rom, key_pressed=0, max_cycles=3000, initial_ram=ram_black)
    screen_drawn_cleared = sum(
        1 for r in range(256) for c in range(SCREEN_WORDS_PER_ROW)
        if ram_cleared[SCREEN_BASE + r * SCREEN_WORDS_PER_ROW + c] != 0
    )
    if screen_drawn_cleared != 0:
        raise AssertionError(f"Expected the box to clear after key release, found {screen_drawn_cleared} non-white words.")
    print(f"    Total black words on screen after release: {screen_drawn_cleared}")
    print("    Result: PASS -> Box cleared instantly!\n")

    print("=" * 65)
    print("ALL BOX PROGRAM TESTS PASSED.")
    print("=" * 65)

if __name__ == "__main__":
    main()
