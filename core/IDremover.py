import glob, os, re

def get_text_files():
    files = sorted(glob.glob("./Files/text_export/*.ipl"))
    return files

def parse_query(raw):
    """Split input into numeric IDs and name prefixes.
    Returns (id_set, name_prefixes_list).
    Tokens that are pure integers → IDs.
    Tokens with letters → name prefixes (case-insensitive).
    """
    tokens = re.split(r'[\s,]+', raw.strip())
    ids = set()
    prefixes = []
    for t in tokens:
        if not t:
            continue
        try:
            ids.add(int(t))
        except ValueError:
            prefixes.append(t.lower())
    return ids, prefixes

def matches_query(parts, ids, prefixes):
    """Return True if this inst line should be removed."""
    try:
        obj_id = int(parts[0])
    except (ValueError, IndexError):
        return False
    if obj_id in ids:
        return True
    if prefixes and len(parts) >= 2:
        model = parts[1].strip().lower()
        if any(model.startswith(p) for p in prefixes):
            return True
    return False


def process_file(lines, remove_ids, remove_prefixes):
    """Remove matching INST lines. Returns (new_lines, removed_count)."""
    new_lines = []
    removed_count = 0
    in_inst = False
    for line in lines:
        stripped = line.strip()
        low = stripped.lower()
        if low == 'inst':
            in_inst = True
            new_lines.append(line)
            continue
        if low in ('end', 'cars'):
            in_inst = False
            new_lines.append(line)
            continue
        if in_inst and stripped and not stripped.startswith('#'):
            parts = [p.strip() for p in stripped.split(',')]
            if matches_query(parts, remove_ids, remove_prefixes):
                removed_count += 1
                continue
        new_lines.append(line)
    return new_lines, removed_count


def main():
    print("ID Remover v1.0\n")

    while True:
        # --- List files ---
        files = get_text_files()
        if not files:
            print("No .ipl files found in text/ folder.")
            input("\nPress Enter to exit...")
            return

        all_idx = len(files) + 1
        print("Files in text/:")
        for i, f in enumerate(files, start=1):
            print(f"  {i}  {os.path.basename(f)}")
        print(f"  {all_idx}  All files")

        # --- Pick file(s) ---
        print()
        raw = input("Enter file number(s)  (e.g. 1  or  1, 3, 4): ").strip()

        tokens = re.split(r'[\s,]+', raw.strip())
        chosen_indices = set()
        valid = True
        for t in tokens:
            if not t:
                continue
            try:
                n = int(t)
                if n < 1 or n > all_idx:
                    raise ValueError
                chosen_indices.add(n)
            except ValueError:
                print(f"  Invalid choice '{t}', enter numbers between 1 and {all_idx}.\n")
                valid = False
                break
        if not valid or not chosen_indices:
            if valid:
                print(f"  Invalid choice, enter numbers between 1 and {all_idx}.\n")
            continue

        if all_idx in chosen_indices:
            selected_files = files
        else:
            selected_files = [files[i - 1] for i in sorted(chosen_indices)]

        # --- Show selection and total entry count ---
        file_lines_cache = {}
        for fp in selected_files:
            with open(fp, 'r') as fh:
                lns = fh.readlines()
            file_lines_cache[fp] = lns

        names_str = ", ".join(os.path.basename(f) for f in selected_files)
        print(f"\nSelected: {names_str}")

        # --- Pick IDs / names to remove ---
        print("  Enter IDs, model names or prefixes (mixed allowed):")
        print("  Examples:  700, 3336, 16683")
        print("             sm_veg, cxref")
        print("             sm_veg 700 cxref")
        raw_input = input("Remove: ").strip()
        if not raw_input:
            print("  Nothing entered.\n")
            continue

        remove_ids, remove_prefixes = parse_query(raw_input)
        if not remove_ids and not remove_prefixes:
            print("  No valid entries parsed.\n")
            continue

        # --- Process each selected file ---
        print("\n========")
        print("Results:")
        for fp in selected_files:
            file_name = os.path.basename(fp)
            lns = file_lines_cache[fp]
            new_lines, removed_count = process_file(lns, remove_ids, remove_prefixes)
            with open(fp, 'w') as fh:
                fh.writelines(new_lines)
            print(f"File name:    {file_name}")
            print(f"Founded ID`s: {removed_count}")
            print(f"Deleted ID`s: {removed_count}")
        print("========\n")

        input("Press Enter to continue...")
        print()

if __name__ == '__main__':
    main()
