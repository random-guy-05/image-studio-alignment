"""Sample pixel colors at detected positions to understand layout."""
import cv2, numpy as np
import json

cap = cv2.imread("/tmp/imagestudio.png")
hsv = cv2.cvtColor(cap, cv2.COLOR_BGR2HSV)
gray = cv2.cvtColor(cap, cv2.COLOR_BGR2GRAY)

blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))
grey_light = cv2.inRange(hsv, np.array((0, 0, 100)), np.array((180, 30, 200)))
grey_dark  = cv2.inRange(hsv, np.array((0, 0, 60)),  np.array((180, 60, 130)))
grey_mask  = cv2.bitwise_or(grey_light, grey_dark)

# Get blue circles
blurred_b = cv2.GaussianBlur(blue_mask, (5, 5), 1)
blue_circles = cv2.HoughCircles(blurred_b, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                                 param1=80, param2=15, minRadius=12, maxRadius=18)
blue_circles = [] if blue_circles is None else [(int(x), int(y), int(r)) for x, y, r in blue_circles[0]]
print(f"Blue circles: {len(blue_circles)}")

# Get grey circles
blurred_g = cv2.GaussianBlur(grey_mask, (5, 5), 1)
grey_circles = cv2.HoughCircles(blurred_g, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                                 param1=80, param2=20, minRadius=8, maxRadius=18)
grey_circles = [] if grey_circles is None else [(int(x), int(y), int(r)) for x, y, r in grey_circles[0]]
print(f"Grey circles: {len(grey_circles)}")

# Sample the actual pixel colors at each blue circle position
print("\nSampled colors at blue positions (BGR, HSV):")
for i, (cx, cy, r) in enumerate(blue_circles[:5]):
    bgr = cap[cy, cx]
    h, s, v = hsv[cy, cx]
    print(f"  blue {i}: pos=({cx},{cy})  BGR={tuple(int(c) for c in bgr)}  HSV=({h},{s},{v})  ring pixel: ", end="")
    # Sample at radius+1
    for ang in [0, 90, 180, 270]:
        import math
        rx, ry = int(cx + (r+2) * math.cos(math.radians(ang))), int(cy + (r+2) * math.sin(math.radians(ang)))
        if 0 <= rx < cap.shape[1] and 0 <= ry < cap.shape[0]:
            print(f"({hsv[ry, rx][0]},{hsv[ry, rx][1]},{hsv[ry, rx][2]})", end=" ")
    print()

print("\nSampled colors at grey positions:")
for i, (cx, cy, r) in enumerate(grey_circles[:5]):
    bgr = cap[cy, cx]
    h, s, v = hsv[cy, cx]
    print(f"  grey {i}: pos=({cx},{cy})  BGR={tuple(int(c) for c in bgr)}  HSV=({h},{s},{v})")

# Check: at each blue circle's position, is there grey underneath?
print("\nGrey pixel density at blue circle positions (inside the circle):")
import math
for i, (cx, cy, r) in enumerate(blue_circles[:10]):
    count = 0
    total = 0
    for dx in range(-r+2, r-1):
        for dy in range(-r+2, r-1):
            if dx*dx + dy*dy > (r-2)**2:
                continue
            x, y = cx+dx, cy+dy
            if 0 <= x < grey_mask.shape[1] and 0 <= y < grey_mask.shape[0]:
                count += 1 if grey_mask[y, x] else 0
                total += 1
    print(f"  blue {i}: ({cx},{cy}) grey_pixels_inside={count}/{total}")
