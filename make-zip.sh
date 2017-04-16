#!/bin/bash

if [ -d "src/venv" ]; then
    if [ -d "makezip" ]; then
        rm -rf makezip
    fi

    if [ -d jawbone.zip ]; then
        rm -rf jawbone.zip
    fi

    mkdir makezip
    cp src/*.py makezip/
    cp -R src/alexa makezip/alexa
    cp -R src/jawbone makezip/jawbone
    cp -R src/venv/lib/python2.7/site-packages/* makezip/
    cd makezip
    zip -r ../jawbone.zip *
    cd ../
    rm -rf makezip
else
    echo "Please setup the virtual environment (venv)"
fi
