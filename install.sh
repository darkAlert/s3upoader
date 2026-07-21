#!/bin/bash
: '
*****************************************
S3Uploader Installer
© AVA, 2025
*****************************************
'
rm -rf ./dist
python3 -m build
pip3 uninstall s3upoader -y
pip3 install dist/s3upoader-0.1.4-py3-none-any.whl
