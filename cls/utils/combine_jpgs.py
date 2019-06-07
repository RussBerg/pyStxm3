import sys
from PIL import Image
import os


def combine_jpgs(jpg_lst, output_fname):
    images = list(map(Image.open, jpg_lst))
    widths, heights = list(zip(*(i.size for i in images)))

    total_width = sum(widths)
    max_height = max(heights)

    new_im = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    for im in images:
      new_im.paste(im, (x_offset,0))
      x_offset += im.size[0]

    new_im.save(output_fname)

if __name__== '__main__':
    image_dir = r'C:\controls\git_sandbox\pyStxm\cls\tests\opencv\images_1'
    img1_nm = os.path.join(image_dir, 'C180207350_084.jpg')
    img2_nm = os.path.join(image_dir, 'C180207350_159.jpg')
    combine_jpgs([img1_nm, img2_nm])
