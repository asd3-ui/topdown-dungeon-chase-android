[app]
title = Top-Down Dungeon Chase
package.name = topdowndungeon
package.domain = org.dungeon.chase
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,ogg,ttf
version = 1.0.0
requirements = python3,pygame==2.6.1
orientation = portrait
fullscreen = 1
permissions = INTERNET, VIBRATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
