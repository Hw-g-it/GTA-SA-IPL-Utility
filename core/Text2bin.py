import struct, glob, os

MAGIC = b"bnry"

# Header: 18 x uint32 (little-endian), placed right after 'bnry'
HEADER_FORMAT = "<18I"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)   # 72 bytes
BASE_OFFSET = 4 + HEADER_SIZE                  # 76 bytes (magic + header)

# Entry formats (little-endian, same layout as Binary2text.py)
INST_FORMAT = "<7f3i"   # posx posy posz rotx roty rotz rotw obj_id interior lod
INST_SIZE = struct.calcsize(INST_FORMAT)        # 40 bytes

CARS_FORMAT = "<4f8i"   # 4 floats + 8 ints
CARS_SIZE = struct.calcsize(CARS_FORMAT)        # 48 bytes


# ----- Functions -----

def get_text_files():
    return glob.glob("./Files/text_export/*.ipl")

def ensure_dir(dir_name):
    os.makedirs(dir_name, exist_ok=True)

def parse_text_ipl(file_path):
    """Parse text IPL and return (inst_lines, cars_lines) as raw string lists."""
    inst_lines = []
    cars_lines = []
    current_section = None
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            lower = line.lower()
            if lower == 'inst':
                current_section = 'inst'
                continue
            if lower == 'cars':
                current_section = 'cars'
                continue
            if lower == 'end':
                current_section = None
                continue
            if current_section == 'inst':
                inst_lines.append(line)
            elif current_section == 'cars':
                cars_lines.append(line)
    return inst_lines, cars_lines

def pack_inst_line(line, line_num):
    """
    Expected format:
        obj_id, model_name, interior, x, y, z, rotx, roty, rotz, rotw, lod
    """
    parts = [p.strip() for p in line.split(',')]
    if len(parts) < 11:
        raise ValueError(f"line {line_num}: expected 11 fields, got {len(parts)}  ->  '{line}'")
    obj_id   = int(parts[0])
    # parts[1] = model name, ignored when packing
    interior = int(parts[2])
    posx     = float(parts[3])
    posy     = float(parts[4])
    posz     = float(parts[5])
    rotx     = float(parts[6])
    roty     = float(parts[7])
    rotz     = float(parts[8])
    rotw     = float(parts[9])
    lod      = int(parts[10])
    return struct.pack(INST_FORMAT,
                       posx, posy, posz, rotx, roty, rotz, rotw,
                       obj_id, interior, lod)

def pack_cars_line(line, line_num):
    """
    Expected format (12 comma-separated values, same as str(tuple)[1:-1]):
        f0, f1, f2, f3, i4, i5, i6, i7, i8, i9, i10, i11
    First 4 are floats, remaining 8 are ints.
    """
    parts = [p.strip() for p in line.split(',')]
    if len(parts) < 12:
        raise ValueError(f"line {line_num}: expected 12 fields, got {len(parts)}  ->  '{line}'")
    f0 = float(parts[0]); f1 = float(parts[1])
    f2 = float(parts[2]); f3 = float(parts[3])
    i4 = int(float(parts[4])); i5 = int(float(parts[5]))
    i6 = int(float(parts[6])); i7 = int(float(parts[7]))
    i8 = int(float(parts[8])); i9 = int(float(parts[9]))
    i10 = int(float(parts[10])); i11 = int(float(parts[11]))
    return struct.pack(CARS_FORMAT, f0, f1, f2, f3, i4, i5, i6, i7, i8, i9, i10, i11)

def build_binary(inst_blobs, car_blobs):
    """Assemble magic + header + inst entries + cars entries into bytes."""
    num_inst = len(inst_blobs)
    num_cars = len(car_blobs)

    offset_inst = BASE_OFFSET if num_inst > 0 else 0
    offset_cars = (offset_inst + num_inst * INST_SIZE) if num_cars > 0 else 0

    header = struct.pack(
        HEADER_FORMAT,
        num_inst, 0, 0, 0,       # num_instances + 3 padding
        num_cars, 0,              # num_cars + padding
        offset_inst, 0,           # offset_inst + padding
        0, 0,                     # offset_unk1 + padding
        0, 0,                     # offset_unk2 + padding
        0, 0,                     # offset_unk3 + padding
        offset_cars, 0,           # offset_cars + padding
        0, 0                      # offset_unk4 + padding
    )

    out = bytearray()
    out += MAGIC
    out += header
    for blob in inst_blobs:
        out += blob
    for blob in car_blobs:
        out += blob

    # Pad to next multiple of 2048 bytes (GTA:SA streaming sector alignment)
    SECTOR = 2048
    remainder = len(out) % SECTOR
    if remainder != 0:
        out += b'\x00' * (SECTOR - remainder)

    return bytes(out)

def convert_text2bin(file_path, out_dir):
    file_name = os.path.basename(file_path)
    print(f"Processing {file_name} ...")

    try:
        inst_lines, cars_lines = parse_text_ipl(file_path)
    except Exception as e:
        print(f"  ERROR reading file: {e}")
        return False

    inst_blobs = []
    for i, line in enumerate(inst_lines, start=1):
        try:
            inst_blobs.append(pack_inst_line(line, i))
        except Exception as e:
            print(f"  ERROR in INST {e}")
            return False

    car_blobs = []
    for i, line in enumerate(cars_lines, start=1):
        try:
            car_blobs.append(pack_cars_line(line, i))
        except Exception as e:
            print(f"  ERROR in CARS {e}")
            return False

    data = build_binary(inst_blobs, car_blobs)
    out_path = os.path.join(out_dir, file_name)
    with open(out_path, 'wb') as f:
        f.write(data)

    print(f"  OK  ->  {out_path}  ({len(inst_blobs)} inst, {len(car_blobs)} cars)")
    return True

def main():
    print("Text2Bin Converter v1.0\n\nPut text IPL files in text/ folder. Press Enter to convert.")
    input()

    ensure_dir("Files/text_export")
    out_dir = "Files/bin_export"
    ensure_dir(out_dir)

    files = get_text_files()
    if not files:
        print("No .ipl files found in text/ folder.")
        print("\nPress Enter to exit...")
        input()
        return

    print(f"Found {len(files)} file(s): {files}\n")

    converted = 0
    failed = 0
    for f in files:
        ok = convert_text2bin(f, out_dir)
        if ok:
            converted += 1
        else:
            failed += 1

    print("\n=========================")
    print("Result:")
    print(f"{converted} - files converted")
    if failed:
        print(f"{failed} - files failed")
    print(f"Output folder: {out_dir}/")
    print("\nPress Enter to exit...")
    input()

# ---------------------
if __name__ == '__main__':
    main()
