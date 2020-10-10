from setuptools import setup

setup(
    name='tracks',
    packages=[
        'tiles',
         'main',
         'utils.grid',
         'utils.lights',
         'utils.mouse',
    ],
    options={
        'build_apps': {
            'include_patterns': [
                'data/*.tmx',
                'data/*.tsx',
                'data/black.png',
                'data/play.png',
                'data/stop.png',
                'models/**/*.dae',
                'thumbs/*.png',
                'config/*.ini',
                'config/*.prc',
            ],
            'gui_apps': {
                'tracks': 'main.py'
            },
            'log_filename': '$USER_APPDATA/Tracks/output.log',
            'log_append': False,
            'plugins': [
                'pandagl',
                'p3assimp',
            ],
            'platforms': [
                'win32',
            ]
        },
    },
)
