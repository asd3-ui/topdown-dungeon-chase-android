[app]

# (str) Title of your application
title = Dungeon Raycast 3D

# (str) Package name
package.name = dungeonraycast

# (str) Package domain (needed for android/ios packaging)
package.domain = org.raycast.dungeon

# (str) Source code where the main.py lives
source.dir = .

# Use the project-local Pygame 2.5.2 recipe
p4a.local_recipes = ./p4a-recipes

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,json

# Keep the web preview and tooling files out of the APK
source.exclude_dirs = src,public,p4a-recipes,.github,node_modules,.git,bin,.buildozer,venv
source.exclude_patterns = package.json,tsconfig.json,metadata.json

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
requirements = python3,pygame

# (str) Supported orientation
orientation = landscape

# (list) Permissions
android.permissions = WAKE_LOCK,VIBRATE

# (int) Target Android API
android.api = 33

# (int) Minimum API
android.minapi = 24

# (str) Android NDK version to use
android.ndk = 25b

# Pin python-for-android release
p4a.branch = v2024.01.21

# (bool) Skip SDK updates
android.skip_update = False

# (bool) Auto accept license
android.accept_sdk_license = True

# (str) Android archs to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) Enable AndroidX support
android.enable_androidx = True

# (str) Presplash background color
android.presplash_color = #0a0a0f

# (str) Window state
android.fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1
