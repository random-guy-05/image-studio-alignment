from PIL import Image
im = Image.open('/tmp/imagestudio2.png')
print('size', im.size, 'mode', im.mode)
