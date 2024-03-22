# A tool that takes in an image and spits out a Phash
import argparse

from PIL import Image
import imagehash

parser = argparse.ArgumentParser()
parser.add_argument("file")

if __name__ == "__main__":
    args = parser.parse_args()
    img = Image.open(args.file)
    print(str(imagehash.phash(img)))
