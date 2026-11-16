import sys
import os

# SET YOUR PERSONAL NUMBER K (last two digits of your roll number)
K = 41  # <-- Replace with your K

PREDEFINED_SYMBOLS = {
    "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
    "R0": 0, "R1": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5, "R6": 6, "R7": 7,
    "R8": 8, "R9": 9, "R10": 10, "R11": 11, "R12": 12, "R13": 13, "R14": 14, "R15": 15,
    "SCREEN": 16384, "KBD": 24576
}

COMP_TABLE = {
    "0":   "0101010", "1":   "0111111", "-1":  "0111010",
    "D":   "0001100", "A":   "0110000", "!D":  "0001101",
    "!A":  "0110001", "-D":  "0001111", "-A":  "0110011",
    "D+1": "0011111", "A+1": "0110111", "D-1": "0001110",
    "A-1": "0110010", "D+A": "0000010", "D-A": "0010011",
    "A-D": "0000111", "D&A": "0000000", "D|A": "0010101",
    "M":   "1110000", "!M":  "1110001", "-M":  "1110011",
    "M+1": "1110111", "M-1": "1110010", "D+M": "1000010",
    "D-M": "1010011", "M-D": "1000111", "D&M": "1000000",
    "D|M": "1010101"
}

DEST_TABLE = {
    "":    "000", "M":   "001", "D":   "010", "MD":  "011",
    "A":   "100", "AM":  "101", "AD":  "110", "AMD": "111"
}

JUMP_TABLE = {
    "":    "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111"
}


def clean_line(raw_line):
    return raw_line.split("//")[0].strip()


def assemble(asm_path, k_val):
    if not os.path.exists(asm_path):
        print(f"Error: File '{asm_path}' not found.")
        return

    with open(asm_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    symbol_table = dict(PREDEFINED_SYMBOLS)
    user_symbols = {}  # Tracks labels and variables for K mod 3 == 0
    cleaned_instructions = []  # Stores (original_line_num, clean_text)
    rom_address = 0
    mode = k_val % 3

    # FIRST PASS: Strip comments/whitespace and record (LABEL) addresses
    for line_num, raw in enumerate(raw_lines, start=1):
        line = clean_line(raw)
        if not line:
            continue

        if line.startswith("(") and line.endswith(")"):
            label = line[1:-1].strip()
            if not label or label[0].isdigit():
                print(f"Line {line_num}: invalid label '{line}'")
                if mode == 1:
                    continue
            if label in symbol_table:
                if mode == 2:
                    print(f"Warning (Line {line_num}): duplicate label '({label})' ignored.")
                continue
            symbol_table[label] = rom_address
            user_symbols[label] = rom_address
        else:
            cleaned_instructions.append((line_num, line))
            rom_address += 1

    # SECOND PASS: Translate A- and C-instructions into 16-bit binary
    next_var_addr = 16
    binary_lines = []
    has_errors = False

    for line_num, inst in cleaned_instructions:
        # A-Instruction: @value or @symbol
        if inst.startswith("@"):
            symbol = inst[1:].strip()
            if not symbol:
                print(f"Line {line_num}: invalid instruction '{inst}'")
                has_errors = True
                continue

            if symbol.isdigit():
                addr = int(symbol)
                if addr < 0 or addr > 32767:
                    print(f"Line {line_num}: address out of range '{inst}'")
                    has_errors = True
                    continue
            else:
                if symbol[0].isdigit():
                    print(f"Line {line_num}: invalid symbol name '{inst}'")
                    has_errors = True
                    continue
                if symbol not in symbol_table:
                    symbol_table[symbol] = next_var_addr
                    user_symbols[symbol] = next_var_addr
                    next_var_addr += 1
                addr = symbol_table[symbol]

            binary_lines.append(f"0{addr:015b}")

        # C-Instruction: [dest=]comp[;jump]
        else:
            dest_part = ""
            jump_part = ""
            comp_part = inst

            if "=" in comp_part:
                parts = comp_part.split("=")
                if len(parts) != 2:
                    print(f"Line {line_num}: invalid instruction '{inst}'")
                    has_errors = True
                    continue
                dest_part, comp_part = parts[0].strip(), parts[1].strip()

            if ";" in comp_part:
                parts = comp_part.split(";")
                if len(parts) != 2:
                    print(f"Line {line_num}: invalid instruction '{inst}'")
                    has_errors = True
                    continue
                comp_part, jump_part = parts[0].strip(), parts[1].strip()

            if (comp_part not in COMP_TABLE or
                dest_part not in DEST_TABLE or
                jump_part not in JUMP_TABLE):
                print(f"Line {line_num}: invalid instruction '{inst}'")
                has_errors = True
                continue

            c_bits = COMP_TABLE[comp_part]
            d_bits = DEST_TABLE[dest_part]
            j_bits = JUMP_TABLE[jump_part]
            binary_lines.append(f"111{c_bits}{d_bits}{j_bits}")

    # K mod 3 == 0: Save all labels and variables with their addresses in symbols.txt
    if mode == 0:
        out_dir = os.path.dirname(os.path.abspath(asm_path))
        sym_path = os.path.join(out_dir, "symbols.txt")
        with open(sym_path, "w", encoding="utf-8") as sf:
            for sym, addr in user_symbols.items():
                sf.write(f"{sym} = {addr}\n")

    if has_errors and mode == 1:
        print("Assembly stopped due to syntax errors.")
        return

    hack_path = os.path.splitext(asm_path)[0] + ".hack"
    with open(hack_path, "w", encoding="utf-8") as out_f:
        out_f.write("\n".join(binary_lines) + ("\n" if binary_lines else ""))
    print(f"Assembled {asm_path} -> {hack_path} ({len(binary_lines)} instructions)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python assembler.py <Program.asm>")
    else:
        assemble(sys.argv[1], K)