# s3up
The s3up uploader continuously watches metafile creation events in a
specific local directory to upload local files to S3 storage in the background.


## Installation
```
git clone https://github.com/darkAlert/s3upoader.git
cd s3upoader
```

### Installation via pip
```
pip3 install git+https://github.com/darkAlert/s3upoader.git#egg=s3upoader
```

### Uninstalling
```
pip3 uninstall s3up -y
```

#### Troubleshooting
Use `--break-system-packages` with the `pip install` command when installing on Debian or Ubuntu 24.04 (and above).
