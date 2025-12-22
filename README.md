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

### Troubleshooting
Use `--break-system-packages` with the `pip install` command when installing on Debian or Ubuntu 24.04 (and above).

### Usage examples
#### Add file(s) to upload
The file will be uploaded to S3 storage in the background:
```
from s3up.s3up import add_to_upload

add_to_upload(src='/path/to/file.mp4', dst='s3://bucket/path/file.mp4', rm_after_upload=True)
```