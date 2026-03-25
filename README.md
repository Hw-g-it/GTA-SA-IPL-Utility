# GTA SA IPL Utility
<img width="853" height="555" alt="image" src="https://github.com/user-attachments/assets/35a8e04e-e763-4675-afe3-ec75589e24ec" />
Я знаю что таких программ немало, но мне нужно было внести некоторые изменения и это вылилось в объединение нескольких функций.

**Bin -> Text** - кидаешь бинарные `.ipl` в `Files/bin_import/`, выбираешь нужные, жмёшь конвертировать. Текстовый IPL появляется в `Files/text_export/`. 
В `bin_import` поместил дефолтные IDE, чтобы переименовать dummy в соответсвующие моделям имена.
При необходимости свои IDE можно поместить туда же.

**Text -> Bin** - обратная операция. Берёт текстовые `.ipl` из `Files/text_export/`, пакует обратно в бинарь с выравниванием по 2048 байт, результат в `Files/bin_export/`.

**ID Remover** - удаляет ненужные строки из текстовых IPL. Вводишь ID, имена моделей или префиксы через запятую, можно вперемешку. Файлы правятся на месте в `Files/text_export/`.

Во всех вкладках работает drag & drop: тащишь `.ipl` на окно, программа проверяет тип файла (бинарный или текстовый) и перекладывает в нужную папку.

## Запуск

```
pip install PyQt5
python IPL_utility.py
```

## Структура папок

```
Files/
  bin_import/    <- бинарные .ipl для конвертации
  text_export/   <- текстовые IPL
  bin_export/    <- результат Text -> Bin
```

## Авторы

- [MadGamerHD](https://github.com/MadGamerHD) — оригинальный декомпилятор ([GTA-SA-Binary-IPL-Inspector](https://github.com/MadGamerHD/GTA-SA-Binary-IPL-Inspector))
- [Shifaau9](https://github.com/Shifaau9) — оригинальный компилятор ([Binary-IPl-Converter](https://github.com/Shifaau9/Binary-IPl-Converter))
- [h.w](https://github.com/Hw-g-it) — доработки и UI

# GTA SA IPL Utility

There are plenty of tools like this, but I needed to make some changes and it ended up merging several functions into one.

**Bin -> Text** - put binary `.ipl` files into `Files/bin_import/`, select them, hit convert. Text IPL shows up in `Files/text_export/`. Default IDE files are included in `bin_import` to resolve dummy names to actual model names. You can drop your own IDE files there too.

**Text -> Bin** - the reverse. Takes text `.ipl` from `Files/text_export/`, packs them back to binary with 2048-byte sector alignment, output goes to `Files/bin_export/`.

**ID Remover** - removes lines from text IPL. Enter IDs, model names or prefixes separated by commas, mixed input works fine. Files are edited in place inside `Files/text_export/`.

Drag & drop works in all tabs: drop a `.ipl` onto the window, the app checks whether it's binary or text and moves it to the right folder.

## Run

```
pip install PyQt5
python IPL_utility.py
```

## Folder structure

```
Files/
  bin_import/    <- binary .ipl input
  text_export/   <- text IPL
  bin_export/    <- Text -> Bin output
```

## Credits

- [MadGamerHD](https://github.com/MadGamerHD) — original decompiler ([GTA-SA-Binary-IPL-Inspector](https://github.com/MadGamerHD/GTA-SA-Binary-IPL-Inspector))
- [Shifaau9](https://github.com/Shifaau9) — original compiler ([Binary-IPl-Converter](https://github.com/Shifaau9/Binary-IPl-Converter))
- [h.w](https://github.com/Hw-g-it) — improvements & UI
