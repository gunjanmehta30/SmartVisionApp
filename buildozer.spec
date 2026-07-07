[app]
title = SmartVisionApp
package.name = smartvisionapp
package.domain = org.amdbyt

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,tflite

version = 0.1
requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.permissions = CAMERA
android.api = 33
android.minapi = 26
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1