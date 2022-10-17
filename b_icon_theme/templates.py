from dataclasses import dataclass, field
from dataclass_wizard import YAMLWizard
from typing import Dict, List, Tuple, Optional
from subprocess import Popen, PIPE
from PIL import ImageColor
from b_theme import load_color_scheme, ColorScheme

import os
import re
import shlex
import math
import glob


CONFIG_DEFAULT_PATH = os.path.expanduser(
    '~/.config/theme/templates/icon-theme/config.yml')
TEMPLATE_DEFAULT_PATH = os.path.expanduser(
    '~/.config/theme/templates/icon-theme/generated')


@dataclass
class IconThemeTemplateConfig(YAMLWizard):
    color_ref: Optional[str] = field(default=None)
    folder_mapings: Dict[str, str] = field(default_factory=dict)


def load_template_configs(path: str = CONFIG_DEFAULT_PATH) -> List[IconThemeTemplateConfig]:
    try:
        config = IconThemeTemplateConfig.from_yaml_file(path)
        return [config] if isinstance(config, IconThemeTemplateConfig) else config
    except Exception as e:
        print('Config error: ', e)
        return []


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


def get_lab_points(color_points: ColorScheme):
    return {name: get_lab(rgb) for name, rgb in vars(color_points).items()}


def extract_dir_colors(dir: str):
    rgb_lab: Dict[str, Tuple[float, float, float]] = {}
    with Popen(shlex.split('egrep -rohI "#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})" "'+dir+'"'), stdout=PIPE, universal_newlines=True) as process:
        if process.stdout:
            for line in process.stdout:
                line = line.strip()
                if line not in rgb_lab:
                    rgb_lab[line] = get_lab(line)
    return rgb_lab


def closest_lab_point(lab_points: Dict[str, Tuple[float, float, float]], lab: Tuple[float, float, float]):
    return min(lab_points.items(), key=lambda p: math.dist(p[1], lab))[0]


def generate_substitutions(lab_points: Dict[str, Tuple[float, float, float]], rgb_labs: Dict[str, Tuple[float, float, float]]):
    subs_6: Dict[str, List[str]] = {}
    subs_3: Dict[str, List[str]] = {}

    for orig, lab in rgb_labs.items():
        sub = closest_lab_point(lab_points, lab)
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


def generate(src_path: str, dest_path: str, substitutions: List[Dict[str, List[str]]]):
    orig_paths = glob.glob(f'{src_path}/**/*.svg', recursive=True)
    print(src_path, len(orig_paths))
    for orig_path in orig_paths:
        filename = orig_path.split('/')[-1]
        try:
            with open(orig_path, 'r') as sf:
                gen_path = os.path.join(dest_path, filename)
                os.makedirs(os.path.dirname(gen_path), exist_ok=True)
                with open(gen_path, 'w+') as df:
                    df.write(substitute(sf.read(), substitutions))
        except Exception as e:
            print(e)


THEME_FILE_HEADER = '''
[Icon Theme]
Name={{ theme_name }}
Comment=Flat dynamic generated icon theme
Inherits=hicolor
Example=folder

KDE-Extensions=.svg
'''

THEME_FILE_DEFAULT_SIZES = '''
DisplayDepth=32
LinkOverlay=link_overlay
LockOverlay=lock_overlay
ZipOverlay=zip_overlay
DesktopDefault=48
DesktopSizes=16,22,32,48,64,96,128,256
ToolbarDefault=22
ToolbarSizes=16,22,32,48
MainToolbarDefault=22
MainToolbarSizes=16,22,32,48
SmallDefault=16
SmallSizes=16,22,32,48
PanelDefault=48
PanelSizes=16,22,32,48,64,96,128,256
DialogDefault=32
DialogSizes=16,22,32,48,64,128,256
FollowsColorScheme=true
'''


def context_name(dir_name: str):
    if dir_name == 'apps':
        return 'Applications'
    if dir_name == 'mimetypes':
        return 'MimeTypes'
    return dir_name.capitalize()


def generate_theme_file(config: IconThemeTemplateConfig):
    dirs = sorted(config.folder_mapings.values())
    dir_listing = ','.join([f'scalable/{dir}' for dir in dirs])
    context_listing = ''.join([f'''
[scalable/{dir}]
Context={context_name(dir)}
Size=64
MinSize=16
MaxSize=512
Type=Scalable
    ''' for dir in dirs])
    path = os.path.join(TEMPLATE_DEFAULT_PATH, 'index.theme')
    with open(path, 'w+') as f:
        f.write(THEME_FILE_HEADER)
        f.write(THEME_FILE_DEFAULT_SIZES)
        f.write(f'\nDirectories={dir_listing}\n')
        f.write(context_listing)


def main():
    for config in load_template_configs():
        scheme = load_color_scheme(config.color_ref)
        lab_points = get_lab_points(scheme)
        for src_path, dest_folder in config.folder_mapings.items():
            try:
                src_path = os.path.expanduser(src_path)
                dest_path = os.path.join(TEMPLATE_DEFAULT_PATH, f'scalable/{dest_folder}')
                rgb_labs = extract_dir_colors(src_path)
                subs = generate_substitutions(lab_points, rgb_labs)
                generate(src_path, dest_path, subs)
            except Exception as e:
                print(e)
        generate_theme_file(config)


if __name__ == "__main__":
    main()
