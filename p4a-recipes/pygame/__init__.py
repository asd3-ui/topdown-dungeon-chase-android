import os
import subprocess
import sys
from os.path import exists, join
from pythonforandroid.logger import info
from pythonforandroid.recipes.pygame import Pygame2Recipe
from pythonforandroid.util import BuildInterruptingException

CYTHON_PIN = "3.0.0"
CYTHON_SERIES = "3.0."

GENERATED_SOURCES = (
    join("src_c", "_sdl2", "audio.c"),
    join("src_c", "_sdl2", "controller.c"),
    join("src_c", "_sdl2", "mixer.c"),
    join("src_c", "_sdl2", "sdl2.c"),
    join("src_c", "_sdl2", "video.c"),
    join("src_c", "_sprite.c"),
    join("src_c", "pypm.c"),
)

class Pygame252Recipe(Pygame2Recipe):
    version = "2.5.2"
    url = "https://github.com/pygame/pygame/archive/{version}.tar.gz"

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        self._generate_cython_sources(self.get_build_dir(arch.arch))

    def _generate_cython_sources(self, build_dir):
        if all(exists(join(build_dir, path)) for path in GENERATED_SOURCES):
            return
        env = self._host_env_with_cython(build_dir)
        subprocess.run([sys.executable, "setup.py", "cython_only"], cwd=build_dir, env=env, check=True)

    def _host_env_with_cython(self, build_dir):
        env = os.environ.copy()
        for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONNOUSERSITE"):
            env.pop(key, None)
        return env

recipe = Pygame252Recipe()
