[app]
title = OneTask
package.name = onetask
package.domain = org.onetask

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav

version = 1.0.0

requirements = python3,kivy==2.3.0,pygame

orientation = portrait

android.permissions = VIBRATE
android.minapi = 31
android.targetapi = 33
android.ndk = 25b
android.sdk = 33
android.archs = arm64-v8a

fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
