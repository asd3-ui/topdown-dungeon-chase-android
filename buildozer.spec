[app]
title = Dungeon Raycast 3D Advanced
package.name = dungeonraycast3d
package.domain = org.dungeon.game
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,ogg,ttf
version = 1.0.0
requirements = python3,kivy==2.3.0,pygame==2.5.2,pyjnius
orientation = landscape
fullscreen = 1
permissions = INTERNET, VIBRATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
icon.filename = %(source.dir)s/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
