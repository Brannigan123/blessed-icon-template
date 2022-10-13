from typing import Dict, List, Tuple
from PIL import ImageColor
from joblib import Parallel, delayed
import shlex
import multiprocessing
from subprocess import Popen, PIPE
import math
import os
import glob
import re

rgb_points = {
    'black':  "#171421",
    'red':  "#E66D76",
    'green': "#5EDEA3",
    'orange': "#EFAB73",
    'blue':  "#73A3DE",
    'magenta': "#D06FE8",
    'cyan':  "#75DBEB",
    'gray':  "#7a7e85",
    'yellow': "#F3D175",
    'white': "#FFFFFF",
}


def get_lab(hexrgb: str):
    rgb = ImageColor.getcolor(hexrgb, "RGB")

    x = rgb[0] * 0.4124 + rgb[1] * 0.3576 + rgb[2] * 0.1805
    y = rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722
    z = rgb[0] * 0.0193 + rgb[1] * 0.1192 + rgb[2] * 0.9505
    xyz = [round(x, 4) / 95.047, round(y, 4) / 100.0, round(z, 4) / 108.883]

    xyz = [v ** (0.3333333333333333) if v >
           0.008856 else (7.787 * v) + (16 / 116) for v in xyz]

    L = (116 * xyz[1]) - 16
    a = 500 * (xyz[0] - xyz[1])
    b = 200 * (xyz[1] - xyz[2])

    Lab = (round(L, 4), round(a, 4), round(b, 4))

    return Lab


lab_points = {
    name: get_lab(rgb) for name, rgb in rgb_points.items()
}


def extract_dir_colors(dir: str):
    rgb_lab: Dict[str, Tuple[float, float, float]] = {}
    with Popen(shlex.split('egrep -roh "#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})" "'+dir+'"'), stdout=PIPE, universal_newlines=True) as process:
        for line in process.stdout:
            line = line.strip()
            if line not in rgb_lab:
                rgb_lab[line] = get_lab(line)
    return rgb_lab


def closest_lab_point(lab: Tuple[float, float, float]):
    return min(lab_points.items(), key=lambda p: math.dist(p[1], lab))[0]


def generate_substitutions(rgb_labs: Dict[str, Tuple[float, float, float]]):
    subs_6: Dict[str, List[str]] = {}
    subs_3: Dict[str, List[str]] = {}

    for orig, lab in rgb_labs.items():
        sub = closest_lab_point(lab)
        subs = subs_3 if len(orig) == 3 else subs_6
        if sub not in subs:
            subs[sub] = []
        subs[sub].append(orig)

    return [subs_6, subs_3]


def substitute(content: str, substitutions: List[Dict[str, List[str]]]):
    for substitutions_set in substitutions:
        for name, colors in substitutions_set.items():
            content = re.sub('|'.join(colors),
                             f'{{{{ theme.colors.{name} }}}}', content)
    return content


def generate(source_path: str, destination_path: str, substitutions: List[Dict[str, List[str]]]):
    orig_paths = glob.glob(f'{source_path}/**/*.svg', recursive=True)
    print(source_path, len(orig_paths))
    for orig_path in orig_paths:
        sub_path = orig_path.replace(source_path, '', 1)
        try:
            with open(orig_path, 'r') as sf:
                gen_path = os.path.join(destination_path, sub_path)
                os.makedirs(os.path.dirname(gen_path), exist_ok=True)
                with open(gen_path, 'w+') as df:
                    df.write(substitute(sf.read(), substitutions))
        except Exception as e:
            print(e)


mappings = { '~/.local/share/icons/hicolor/0x0/apps/': '~/.config/theme/templates/icon-theme/generated/scalable/apps/',
    '~/.local/share/icons/hicolor/16x16/apps/': '~/.config/theme/templates/icon-theme/generated/scalable/apps/',
    '~/.local/share/icons/hicolor/24x24/apps/': '~/.config/theme/templates/icon-theme/generated/scalable/apps/',
    '~/.local/share/icons/hicolor/32x32/apps/': '~/.config/theme/templates/icon-theme/generated/scalable/apps/',
    '~/.local/share/icons/hicolor/48x48/apps/': '~/.config/theme/templates/icon-theme/generated/scalable/apps/',
    '~/.local/share/icons/hicolor/64x64/apps/': '~/.config/theme/templates/icon-theme/generated/scalable/apps/',
    '~/.local/share/icons/hicolor/96x96/apps/': '~/.config/theme/templates/icon-theme/generated/scalable/apps/',
    '~/.local/share/icons/hicolor/128x128/apps/': '~/.config/theme/templates/icon-theme/generated/scalable/apps/',
    '~/.local/share/icons/hicolor/256x256/apps/': '~/.config/theme/templates/icon-theme/generated/scalable/apps/',
    '~/.local/share/icons/hicolor/512x512/apps/': '~/.config/theme/templates/icon-theme/generated/scalable/apps/',
    '~/.local/share/icons/hicolor/1024x1024/apps/': '~/.config/theme/templates/icon-theme/generated/scalable/apps/',
    '~/.local/share/icons/Catppuccin/actions/24/': '~/.config/theme/templates/icon-theme/generated/scalable/actions/',
    '~/.local/share/icons/Catppuccin/devices/22/': '~/.config/theme/templates/icon-theme/generated/scalable/devices/',
    '~/.local/share/icons/Catppuccin/emblems/48/': '~/.config/theme/templates/icon-theme/generated/scalable/emblems/',
    '~/.local/share/icons/Catppuccin/mimetypes/64/': '~/.config/theme/templates/icon-theme/generated/scalable/mimetypes/',
    '~/.local/share/icons/Catppuccin/panel/24/': '~/.config/theme/templates/icon-theme/generated/scalable/panel/',
    '~/.local/share/icons/Catppuccin/places/64/': '~/.config/theme/templates/icon-theme/generated/scalable/places/',
    '~/.local/share/icons/WhiteSur/status/24/': '~/.config/theme/templates/icon-theme/generated/scalable/status/',
    '~/.local/share/icons/WhiteSur/animations/24/': '~/.config/theme/templates/icon-theme/generated/scalable/animations/',
    '~/.local/share/icons/Nordic-Darker/Places/': '~/.config/theme/templates/icon-theme/generated/scalable/places/',
    '~/.local/share/icons/Nordic-Darker/devices/48/': '~/.config/theme/templates/icon-theme/generated/scalable/devices/',
    '~/.local/share/icons/Nordic-Darker/categories/22/': '~/.config/theme/templates/icon-theme/generated/scalable/categories/',
    '~/.local/share/icons/Papirus-Colors/128x128/places/': '~/.config/theme/templates/icon-theme/generated/scalable/places/',
    '~/.local/share/icons/WhiteSur/apps/scalable//': '~/.config/theme/templates/icon-theme/generated/scalable/apps/',
    '~/.local/share/icons/Catppuccin/apps/64/': '~/.config/theme/templates/icon-theme/generated/scalable/apps/',
    '~/.local/share/icons/Fluent-grey-dark/scalable/apps/': '~/.config/theme/templates/icon-theme/generated/scalable/apps/',
    '~/.local/share/icons/WhiteSur-grey-dark/places/scalable/': '~/.config/theme/templates/icon-theme/generated/scalable/places/',
}

for source_path, destination_path in mappings.items():
    source_path = os.path.expanduser(source_path)
    destination_path = os.path.expanduser(destination_path)
    rgb_labs = extract_dir_colors(source_path)
    subs = generate_substitutions(rgb_labs)
    generate(source_path, destination_path, subs)
