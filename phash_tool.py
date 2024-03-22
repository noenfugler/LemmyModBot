# A tool that takes in an image and spits out a Phash
import argparse
from io import BytesIO

import requests
from PIL import Image
import imagehash

parser = argparse.ArgumentParser()
parser.add_argument("--file", "-f", dest="file", help="A local file to load and process")
parser.add_argument("--url", "-u", dest="url", help="A remote file to load and process")


def main():
    args = parser.parse_args()

    if args.file is None and args.url is None:
        print("Must set either input file or url!")
        return

    img = None
    if args.file is not None:
        img = Image.open(args.file)
    elif args.url is not None:
        img = Image.open(BytesIO(requests.get(args.url).content))

    print(str(imagehash.phash(img)))

if __name__ == "__main__":
    main()
