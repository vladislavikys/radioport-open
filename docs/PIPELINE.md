# Как данные добываются из игры

> Все шаги ниже выполняет `py build.py` в корне репозитория. Этот документ объясняет, что происходит внутри.

Все пути ниже заданы переменными: `GAME` = папка игры, `WORK` = рабочая папка (`work/`), `SITE` = `site/`.
Архивы лежат в `GAME\archive\pc\content\`. Для краткости `WK` = `WolvenKit.CLI.exe`, `V` = `vgmstream-cli.exe`.

> **Заметка по WolvenKit.** Папка вывода (`-o`) должна существовать заранее, иначе будет ошибка «Please fill in an output path».
> `-w` принимает шаблон пути, `-r` регулярное выражение.

## Как устроено радио в файлах игры

- Музыка станций лежит в банке `radio.bnk` (Wwise, версия 150). В нём события `mus_radio_NN_<жанр>_<песня>`.
  Событие → действие → музыкальный сегмент → музыкальный трек → id потокового источника.
  Сами песни это `media\<id>.wem` в `audio_2_soundbanks.archive`.
- `NN` в имени события это станция: 01 Morro Rock, 02 Vexelstrom, 03 Night FM, 04 The Dirge, 05 Body Heat, 06 Samizdat,
  07 PEBKAC, 08 Royal Blue, 09 Pacific Dreams, 10 30 Principales, 11 Ritual, 12 Growl FM, 13 Dark Star, 14 Impulse.
  Два трека лежат в `cp_music.bnk` как `mus_custom_radio_*` (Ratatata, When It's War) и добавлены вручную к The Dirge.
- Имена событий в банках хранятся как FNV-1 (32 бита, строчные буквы). Имена берутся из строк в `eventsmetadata.json`.
- Названия песен («артист - название») лежат в английской локализации: ключи `Gameplay-Devices-Radio_tracks-*` в `onscreens.json`.

## Шаги

1. **Банки и метаданные**
   ```
   WK extract audio_2_soundbanks.archive -o WORK\raw -w "*\radio.bnk"
   WK extract audio_2_soundbanks.archive -o WORK\raw -w "*\cp_music.bnk"
   WK extract audio_1_general.archive    -o WORK\raw -w "*sound\event\*.json"
   ```
   (Для поиска событий по всем банкам: `-r "soundbanks\\[^\\]+\.bnk$"` в `WORK\banks`.)
2. **События → источники.** `py pipeline/map.py` строит `radio_map.json`, затем `py pipeline/songs.py` даёт `songs.json`
   (событие → id wem). Готовый результат лежит в `pipeline/data/songs.json`.
3. **Сами песни.** Достать wem по списку id (WK принимает регулярное выражение со списком id) и конвертировать:
   ```
   WK extract audio_2_soundbanks.archive -o WORK\wem -r "media\\(id1|id2|...)\.wem$"
   py pipeline/convert.py        # vgmstream -> wav -> ffmpeg (libmp3lame -q:a 1) -> site/audio
   ```
4. **Названия.** Английская локализация:
   ```
   WK extract lang_en_text.archive -o WORK\loc -w "*onscreens*"
   WK convert serialize WORK\loc\base\localization\en-us\onscreens\onscreens.json -o WORK\locjson
   ```
   Из `Gameplay-Devices-Radio_tracks-*` получается соответствие «событие → название». Часть имён событий не совпадает
   с ключами и сопоставлена вручную. Итог в `pipeline/data/tracks_manifest.json` (станция, файл, название, длительность).
5. **Громкость.** `py pipeline/loudness.py` замеряет интегральную громкость (ffmpeg `ebur128`) в `loudness.json`.
   `build_data.py` берёт 20-й перцентиль как цель и пишет для каждой песни поправку `g` в дБ (только приглушение,
   потому что громкость элемента `<audio>` не поднимается выше 1).
6. **Данные сайта.** `py pipeline/build_data.py` берёт манифесты из `pipeline/data/` и пишет `site/data/tracks.js`.
7. **DJ-реплики.** Субтитры лежат в `lang_en_text.archive` (`subtitles\media\radio\radio_01_conspiracy.json`, `radio_growl.json`),
   `stringId` в hex совпадает с суффиксом имени wem. Голос Max Mike в `audio_1_general.archive` (`vo\radio_max_mike*`),
   Эша в `lang_en_voice.archive` (`vo\ash_radio_growl*`). `py pipeline/build_dj.py` приводит их к уровню музыки (loudnorm)
   и пишет `site/dj/` и `site/data/dj.js`.
8. **Звуки меню.** Эффекты UI хранятся в `sfx_container.bnk` и упакованы в `.opuspak`. Формат `sfx_container.opusinfo`:
   `'SND '`, версия, 0, n1, n2 (20 байт), затем n1 × u32 id звуков, n1 × u16 номер пака, n1+1 × u32 смещения
   (размер звука = следующее смещение в том же паке − текущее). Срез это валидный Wwise-Opus, его декодирует vgmstream.
   `py pipeline/uitree.py` находит источники событий, `py pipeline/extract_ui.py` режет и конвертирует в `site/sfx/*.wav`.
9. **Логотипы, шрифты, иконки.** `py pipeline/extract_assets.py` (см. README).

## Что не получилось

В локализации есть около 27 названий песен (Lick Switch, Reviscerator и др.), для которых в версии 2.31 нет музыкальных событий.
Событие `mus_radio_12_nebula` ссылается на объект, которого нет ни в одном банке. Эти треки в игровых файлах отсутствуют.
