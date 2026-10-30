import os
import subprocess
import sys
from os.path import exists, join
from pythonforandroid.logger import info
from pythonforandroid.recipes.pygame import Pygame2Recipe

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
        build_dir = self.get_build_dir(arch.arch)
        self._patch_android_setup_template(build_dir)
        super().prebuild_arch(arch)
        self._verify_setup_file(build_dir)
        self._generate_cython_sources(build_dir)

    def _patch_android_setup_template(self, build_dir):
        """
        Pygame 2.5.2 moved SIMD surface blitter implementations into
        src_c/simd_blitters_sse2.c and src_c/simd_blitters_avx2.c, which are
        called by src_c/surface.c and src_c/alphablit.c, but Pygame's
        buildconfig/Setup.Android.SDL2.in was never updated to compile them.
        Without them, pygame/surface.so has 29 unresolved symbols on arm64-v8a
        (and 14 on armeabi-v7a), causing dlopen(surface.so) to fail and
        crashing pygame.display.init() on Android startup.
        Also adds -lm so math symbols (sincos, floor, round, pow, atan2)
        have an explicit DT_NEEDED entry for libm.so on Android's linker.
        """
        template_path = join(build_dir, "buildconfig", "Setup.Android.SDL2.in")
        if not exists(template_path):
            return

        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        old_surface = "surface src_c/surface.c src_c/alphablit.c src_c/surface_fill.c $(SDL) $(DEBUG)"
        new_surface = (
            "surface src_c/simd_blitters_sse2.c src_c/simd_blitters_avx2.c "
            "src_c/surface.c src_c/alphablit.c src_c/surface_fill.c $(SDL) $(DEBUG)"
        )
        if old_surface in content and "simd_blitters_sse2.c" not in content:
            content = content.replace(old_surface, new_surface)

        old_sdl = "SDL = {sdl_includes} -D_REENTRANT -DSDL2 -lSDL2"
        new_sdl = "SDL = {sdl_includes} -D_REENTRANT -DSDL2 -lSDL2 -lm"
        if old_sdl in content and "-lSDL2 -lm" not in content:
            content = content.replace(old_sdl, new_sdl)

        with open(template_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _verify_setup_file(self, build_dir):
        setup_path = join(build_dir, "Setup")
        if not exists(setup_path):
            return
        with open(setup_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "simd_blitters_sse2.c" not in content:
            content = content.replace(
                "surface src_c/surface.c src_c/alphablit.c src_c/surface_fill.c",
                "surface src_c/simd_blitters_sse2.c src_c/simd_blitters_avx2.c src_c/surface.c src_c/alphablit.c src_c/surface_fill.c",
            )
            with open(setup_path, "w", encoding="utf-8") as f:
                f.write(content)
        info("Verified Pygame Setup includes simd_blitters_sse2.c and simd_blitters_avx2.c")

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
