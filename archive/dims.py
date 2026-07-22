from PIL import Image
im = Image.open('/tmp/imagestudio.png')
print('size', im.size, 'mode', im.mode)
