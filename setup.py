from setuptools import setup, find_packages

VERSION = '0.0.1'
DESCRIPTION = 'Package for icon templates using b_theme'
LONG_DESCRIPTION = 'Package for icon templates using b_theme'

packages = find_packages()
package_data = {package: ["py.typed"] for package in packages}


setup(
    name="b_icon_theme",
    version=VERSION,
    author="Brannigan Sakwah",
    author_email="brannigansakwah@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=packages,
    package_data=package_data,
    entry_points={
        'console_scripts': [
            'update_b_icon_theme = b_icon_theme.templates:main'
        ]
    },
    install_requires=[
        'b_theme',
        'jinja2',
        'dataclass_wizard'
    ],
    keywords=['python', 'theme', 'icon', 'config', 'template', 'dynamic'],
)
