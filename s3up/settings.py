
def _username():
    import getpass
    return getpass.getuser()


PKJ_NAME = 's3up'
S3_CMD = 'aws s3'
WATCH_DIR = f'/home/{_username()}/.{PKJ_NAME}'

CMD_UPLOAD = 'upload'
CMD_ADD = 'add'
CMD_WATCH = 'watch'
