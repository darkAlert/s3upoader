"""
The s3up uploader continuously monitors file creation events in a
specific local directory to upload them to S3 storage in the background.
© AVA, 2025
"""
from s3up.s3up import main


if __name__ == '__main__':
    main()
