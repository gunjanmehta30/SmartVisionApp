[app]
title = SmartVisionApp
package.name = smartvisionapp
package.domain = org.amdbyt

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,onnx
source.include_patterns = assets/*

version = 0.2
requirements = hostpython3, python3, kivy, numpy==1.23.5, opencv, plyer

orientation = portrait
fullscreen = 0

android.permissions = CAMERA
android.api = 33
android.minapi = 26
android.ndk = 28c

android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1