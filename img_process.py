from PIL import Image
from fastapi import UploadFile
import io
from pathlib import Path

def crop_and_save(file: UploadFile, folder: str):
    content = file.file.read()
    im = Image.open(io.BytesIO(content))
    width, height = im.size
    temp = None
    arr: list[int] = [0] 
    for i in range(height):
        rgb = im.getpixel(xy=(1,i))
        if rgb != temp and i - arr[-1] > 5:
            arr.append(i)
        temp = rgb
    top, bottom = arr[2], arr[-2]

    cropped = im.crop([0, top, width, bottom])
    Path("screenshots/{}".format(folder)).mkdir(parents=True, exist_ok=True)
    cropped.save("screenshots/{}/{}".format(folder, file.filename))