[app]
title = Top-Down Dungeon Chase
package.name = topdowndungeonchase
package.domain = org.asd3
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,ogg,ttf
version = 1.0.0
requirements = python3,hostpython3,pygame==2.6.1
orientation = landscape
fullscreen = 1
permissions = INTERNET, VIBRATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a
icon.filename = %(source.dir)s/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
