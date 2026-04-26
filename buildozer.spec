[app]
title = OneTask
package.name = onetask
package.domain = org.onetask

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,db

version = 1.0.0

requirements = python3,kivy==2.3.0,sqlite3,pygame

orientation = portrait

# Android permissions
android.permissions = VIBRATE,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE

android.minapi = 29
android.targetapi = 33
android.ndk = 25b
android.sdk = 33

android.archs = arm64-v8a, armeabi-v7a

# App icon (add your icon.png to root folder later)
# icon.filename = %(source.dir)s/assets/icon.png

fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
