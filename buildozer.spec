name: Build OneTask APK

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-22.04
    timeout-minutes: 120

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Force Java 17
        run: |
          sudo apt-get install -y openjdk-17-jdk
          sudo update-alternatives --set java /usr/lib/jvm/java-17-openjdk-amd64/bin/java
          sudo update-alternatives --set javac /usr/lib/jvm/java-17-openjdk-amd64/bin/javac
          echo "JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64" >> $GITHUB_ENV
          java -version

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            git zip unzip \
            autoconf libtool pkg-config \
            zlib1g-dev libncurses5-dev libncursesw5-dev \
            cmake libffi-dev libssl-dev libltdl-dev

      - name: Install Python build tools
        run: |
          pip install --upgrade pip setuptools wheel
          pip install buildozer==1.5.0
          pip install cython==0.29.33

      - name: Generate sound files
        run: python generate_sounds.py

      - name: Cache Buildozer
        uses: actions/cache@v4
        with:
          path: ~/.buildozer
          key: ${{ runner.os }}-buildozer-v2-${{ hashFiles('buildozer.spec') }}
          restore-keys: |
            ${{ runner.os }}-buildozer-v2-

      - name: Build APK
        run: yes | buildozer -v android debug 2>&1
        env:
          JAVA_HOME: /usr/lib/jvm/java-17-openjdk-amd64

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: OneTask-APK
          path: bin/*.apk
          retention-days: 30