import struct,glob,os

header_format = "4s18i"
header_size = struct.calcsize(header_format)

inst_format = "7f3i"
inst_size = struct.calcsize(inst_format)

cars_format = "4f8i"
cars_size = struct.calcsize(cars_format)


def load_ide_models():
    """
    1. Загружает bin/DefaultIDE/default_models.ide (быстрый индекс, формат: id, name).
    2. Затем рекурсивно сканирует все .ide в bin/ и подпапках (кроме DefaultIDE)
       для подхвата кастомных IDE (перезаписывают дефолт).
    """
    model_map = {}

    # --- Шаг 1: дефолтный индекс ---
    default_file = "./Files/bin_import/DefaultIDE/default_models.ide"
    if os.path.exists(default_file):
        with open(default_file, 'r', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 2:
                    try:
                        model_map[int(parts[0])] = parts[1]
                    except ValueError:
                        pass

    # --- Шаг 2: кастомные IDE в bin/ рекурсивно (пропускаем DefaultIDE) ---
    section_with_id = {'objs', 'tobj', 'anim', 'weap', 'cars', 'peds', 'hier'}
    default_dir = os.path.normpath("./Files/bin_import/DefaultIDE")
    for ide_path in glob.glob("./Files/bin_import/**/*.ide", recursive=True):
        if os.path.normpath(os.path.dirname(ide_path)) == default_dir:
            continue
        with open(ide_path, 'r', errors='ignore') as f:
            in_section = False
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.lower() in section_with_id:
                    in_section = True
                    continue
                if line.lower() == 'end':
                    in_section = False
                    continue
                if in_section:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 2:
                        try:
                            model_map[int(parts[0])] = parts[1]
                        except ValueError:
                            pass
    return model_map




# ----- Functions -----

def get_files_with_extention(str_extention):
    str_extention = "./Files/bin_import/*." + str_extention
    return glob.glob(str_extention)

def file_dir(dirName,fileName):
    os.makedirs(dirName, exist_ok=True)
    if os.path.exists(dirName+"/"+fileName):
        os.remove(dirName+"/"+fileName)

def checks(file_names):
    global header_size
    model_map = load_ide_models()
    print("Loaded " + str(len(model_map)) + " model(s) from IDE files.")
    dummy_lines = []
    files_converted = 0
    for y in file_names:
        file_name = os.path.basename(y)
        with open(y, 'rb') as f:
            try:
                data = struct.unpack(header_format,f.read()[:header_size])
            except:
                print("\nError opening file (" + file_name +")! Press return to restart program...\n\n-----\n\n\n")
                main()
                
            print("Successfully opened file (" + file_name +").")

            convert_bin2text(data[1],data[5],file_name,y,model_map,dummy_lines)
            files_converted += 1
        header_size = struct.calcsize(header_format)

    print("=========================")
    print("Result:")
    print(str(files_converted) + " - files converted")
    print(str(len(dummy_lines)) + " - model name not founds")
    for line in dummy_lines:
        print(line)
     

def convert_bin2text(inst_instances,car_instances,file_name,input_file,model_map,dummy_lines):
    global header_size
    file_dir("Files/text_export",file_name)
    line_number = 1  # starts after the 2 header lines (comment + 'inst')

    with open("Files/text_export/"+file_name, 'a+') as w:
        w.write("# This file has been converted using Bin2Text Converter by Grinch_ \ninst\n")
        for x in range(inst_instances):
            with open(input_file, 'rb') as r:
                try:
                    data = struct.unpack(inst_format,r.read()[header_size:(header_size+40)])
                except:
                    print("\nError processing inst of file (" + file_name +")! Press return to restart program...\n\n-----\n\n\n")
                    input()
                    main()

                obj_id = data[7]
                model_name = model_map.get(obj_id, 'dummy')
                if model_name == 'dummy':
                    dummy_lines.append(file_name + " : line " + str(line_number) + " (id " + str(obj_id) + ")")
                text_ipl = '{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}'.format(
                    obj_id, model_name, data[8],
                    repr(data[0]), repr(data[1]), repr(data[2]),
                    repr(data[3]), repr(data[4]), repr(data[5]), repr(data[6]),
                    data[9])
                w.write(text_ipl)
                w.write("\n")
                line_number += 1
            header_size += 40
        w.write("end\ncars\n")
        for x in range(car_instances):
            with open(input_file, 'rb') as r:
                try:
                    data = struct.unpack(cars_format,r.read()[header_size:(header_size+48)])
                except:
                    print("\nError processing car of (" + file_name +")! Press return to restart program...\n\n-----\n\n\n")
                    input()
                    main()
                w.write(''.join(str(data)[1:-1]))
                w.write("\n")
                    
            header_size += 48
        w.write("end\n")
    print("Successfully processed file (" + file_name +").\n")

def main():
    print("Bin2Text converter 2.0, updated by H.W\n\nPut all the binary ipl files in bin folder. Press enter to convert.")
    input()
    if not os.path.exists("Files/bin_import"):
        os.makedirs("Files/bin_import", exist_ok=True)
        print("bin_import directory doesn't seem to exist. Creating it.")

    file_names = get_files_with_extention("ipl")
    if len(file_names) != 0 :
        print("Found IPL files: " + str(file_names) + "\n")
        checks(file_names)
    else:
        print("No IPL files found")
    print("Press return to restart...")
    input()
    main()
# ---------------------


#----Main-----s
if __name__ == '__main__':
    main()
    print("\nTask completed successfully.")