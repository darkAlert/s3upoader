"""
The s3up uploader continuously watches metafile creation events in a
specific local directory to upload local files to S3 storage in the background.
© AVA, 2025
"""
import os
import argparse
import json
import threading

import inotify_simple
import suproc.suproc as suproc

from s3up.utils.logger import Logger
from s3up.utils.utils import get_unique_id
from s3up.utils.queue_wrapper import QueueWrapper
from s3up.settings import PKJ_NAME, S3_CMD, WATCH_DIR, CMD_UPLOAD, CMD_ADD, CMD_WATCH


def upload_file_to_s3(file_path, s3_url, logger=None):
    """
    Upload a local file to S3 storage.

    Args:
        file_path (str): Path to the local file to upload.
        s3_url (str): The URL of the S3 storage where the local file will be uploaded.
        logger (object): A logger to output logs.
    """
    # Command to execute:
    cmd = f"{S3_CMD} cp {file_path} {s3_url}"

    if suproc.run_single_instance_proc(name=PKJ_NAME, logger=logger, cmds=[cmd]) >= 0:
        return 0
    else:
        return -1


def watch(watch_dir=WATCH_DIR, qmaxsize=2000):
    """
    Continuously watches metafile creation events to upload local files to S3 storage.

    Args:
        watch_dir (str): The directory where the metafile will be saved and where the watcher will watch events.
        qmaxsize (int): Max size of the upload queue.
    """
    logger = Logger.get_logger(PKJ_NAME)

    # Ensure the directory exists:
    os.makedirs(watch_dir, exist_ok=True)

    # Create an inotify instance and add a watch:
    inotify = inotify_simple.INotify()
    mask = inotify_simple.flags.CLOSE_WRITE
    wd = inotify.add_watch(watch_dir, mask)      # watch descriptor
    logger.info(f"Watching directory: {watch_dir}")

    # Init upload queue and worker thread:
    upload_queue = QueueWrapper(qmaxsize=qmaxsize)
    thread = threading.Thread(target=_upload_worker, args=(upload_queue, logger))
    thread.start()

    # Get all metafiles in the watch_dir and put them to upload_queue::
    for file in os.listdir(watch_dir):
        metafile_path = os.path.join(watch_dir, file)
        if os.path.isfile(metafile_path):
            upload_queue.put(metafile_path)

    # Infinite loop:
    try:
        while True:
            # Read events (blocks until events occur):
            for event in inotify.read():
                flags = inotify_simple.flags.from_mask(event.mask)
                flag_names = f"{', '.join([flag.name for flag in flags])}"
                metafile_path = os.path.join(watch_dir, event.name)
                logger.info(f"[event: {flag_names}, filename: {metafile_path}")

                # Put to upload:
                upload_queue.put(metafile_path)

    except KeyboardInterrupt:
        logger.warning(f"KeyboardInterrupt")
    except Exception as e:
        logger.error(f"An error occurred:")
        logger.error(e)

    # Close and join:
    inotify.rm_watch(wd)
    inotify.close()
    upload_queue.terminate()
    thread.join()
    logger.info(f"Stopped watching.")


def _upload_worker(queue, logger):
    while not queue.stop_event.is_set():
        # Get metafile path:
        metafile_path = queue.get()

        try:
            # Read a file containing metadata:
            with open(metafile_path, 'r') as f:
                metadata = json.load(f)
            rm_after_upload = metadata.get('rm', False)

            # Read the metadata and upload files to s3:
            for file_path, s3_url in zip(metadata['src'], metadata['dst']):
                logger.info(f"Uploading {file_path} to {s3_url} ...")

                if upload_file_to_s3(file_path, s3_url, logger=logger) == 0:
                    logger.info(f"Uploaded successfully!")

                    # Remove the file:
                    if rm_after_upload:
                        os.remove(file_path)
                else:
                    logger.warning(f"Upload failed!")

            # Remove metafile:
            os.remove(metafile_path)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            logger.error(f"Failed to read metadata: {metafile_path}")
            print(e)
            continue


def add_to_upload(src, dst, rm_after_upload=False, watch_dir=WATCH_DIR):
    """
    Add a file(s) to upload. This file(s) will be uploaded to S3 storage in the background.

    Args:
        src (str or list[str]): The source file or list of files to be uploaded.
        dst (str or list[str]): The URL of the S3 storage where the files will be uploaded.
        rm_after_upload (bool): Remove the source file after it has been successfully uploaded.
        watch_dir (str): The directory where the metafile will be saved and where the watcher will watch events.
    """
    if not isinstance(src, list):
        src = [src]
    if not isinstance(dst, list):
        dst = [dst]
    assert len(src) == len(dst)

    # Run the watching if it is not running:
    if not suproc.is_running(PKJ_NAME):
        run_watching(watch_dir=watch_dir)

    # Generate metadata:
    metadata = {'src': src, 'dst': dst, 'rm': rm_after_upload}

    while True:
        meta_path = os.path.join(watch_dir, str(get_unique_id()))

        if not os.path.exists(meta_path):
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=3)

            return True


def run_watching(watch_dir=WATCH_DIR, qmaxsize=2000, daemon=False, suproc_wrap=True, restart=False):
    """
    Run the watching.

    Args:
        watch_dir (str): The directory where the metafile will be saved and where the watcher will watch events.
        qmaxsize (int): Max size of the upload queue.
        daemon (bool): Run in background as a daemon.
        suproc_wrap (bool): Use the suproc wrapper. It prevents multiple watch instances from running simultaneously.
        restart (bool): Restart the process if it is running.
    """
    if suproc_wrap:
        logger = Logger.get_logger(PKJ_NAME)
        cmd = f"{PKJ_NAME} {CMD_WATCH} --watch-dir={watch_dir} --qmaxsize={qmaxsize} --no-suproc"
        suproc.run_single_instance_proc(name=PKJ_NAME, logger=logger, daemon=daemon, force=restart, cmds=[cmd])
    else:
        watch(watch_dir=watch_dir, qmaxsize=qmaxsize)


def main():
    # Create a parser:
    parser = argparse.ArgumentParser(
        's3up',
        description='Continuously watches metafile creation events to upload local files to S3 storage.'
    )
    parser.add_argument(
        '-v', '--version', action='store_true', default=False,
        help=f"Show the package version"
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create a common (parent) parser (containing common arguments for subparsers):
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        '-wd', '--watch-dir', type=str, default=PKJ_NAME,
        help='The directory where the metafile will be saved and where the watcher will watch events.'
    )

    # Create a subparser for the 'CMD_UPLOAD' command:
    parser_upload = subparsers.add_parser(
        CMD_UPLOAD, parents=[parent_parser],
        help=f"Instantly upload a local file to S3 storage."
    )
    parser_upload.add_argument(
        '--src', type=str, default=None, required=True,
        help='Path to the local file to upload.'
    )
    parser_upload.add_argument(
        '--dst', type=str, default=None, required=True,
        help='The URL of the S3 storage where the local file will be uploaded.'
    )

    # Create a subparser for the 'CMD_ADD' command:
    parser_add = subparsers.add_parser(
        CMD_ADD, parents=[parent_parser],
        help=f"Add a file(s) to upload. This file(s) will be uploaded to S3 storage in the background."
    )
    parser_add.add_argument(
        '--src', type=str, default=None, required=True,
        help='Path to the local file to upload.'
    )
    parser_add.add_argument(
        '--dst', type=str, default=None, required=True,
        help='The URL of the S3 storage where the local file will be uploaded.'
    )
    parser_add.add_argument(
        '--rm', action='store_true', default=False,
        help='Remove the source file after it has been successfully uploaded.'
    )

    # Create a subparser for the 'WATCH' command:
    parser_watch = subparsers.add_parser(
        CMD_WATCH, parents=[parent_parser],
        help=f"Continuously watches metafile creation events to upload local files to S3 storage."
    )
    parser_watch.add_argument(
        '--qmaxsize', type=int, default=2000,
        help='Max size of the upload queue.'
    )
    parser_watch.add_argument(
        '-d', '--daemon', action='store_true', default=False,
        help='Run in background as a daemon.'
    )
    parser_watch.add_argument(
        '--no-suproc', action='store_true', default=False,
        help='Do not use the suproc wrapper. This may result in multiple instances of the s3up running simultaneously.'
    )
    parser_watch.add_argument(
        '--restart', action='store_true', default=False,
        help='Restart the process if it is running.'
    )

    args = parser.parse_args()

    # Run commands:
    if args.version:
        # Show version and exit:
        from s3up import __version__
        Logger.get_logger(PKJ_NAME).info(__version__)
        exit(0)
    elif args.command == CMD_UPLOAD:
        upload_file_to_s3(
            file_path=args.src,
            s3_url=args.dst
        )
    elif args.command == CMD_ADD:
        add_to_upload(
            src=args.src,
            dst=args.dst,
            rm_after_upload=args.rm,
            watch_dir=args.watch_dir
        )
    elif args.command == CMD_WATCH:
        # Run the watching:
        run_watching(
            watch_dir=args.watch_dir,
            qmaxsize=args.qmaxsize,
            daemon=args.daemon,
            suproc_wrap=not args.no_suproc
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
