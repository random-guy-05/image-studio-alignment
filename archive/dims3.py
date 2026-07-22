from PIL import Image
print('window:', Image.open('/tmp/window-now.png').size)
print('full:  ', Image.open('/tmp/full-now.png').size)
