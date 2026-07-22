"""Try much tighter grey detection — must actually be grey (S near 0, neutral)."""
import cv2, numpy as np

cap = cv2.imread("/tmp/imagestudio.png")
hsv = cv2.cvtColor(cap, cv2.COLOR_BGR2HSV)

# Strict grey: low saturation (true grey has no hue)
mask_strict_grey = cv2.inRange(hsv, np.array((0, 0, 60)), np.array((180, 15, 220)))

# Range 1: pure grey (S<10)
mask_pure = cv2.inRange(hsv, np.array((0, 0, 50)), np.array((180, 10, 220)))
# Range 2: very light grey
mask_light = cv2.inRange(hsv, np.array((0, 0, 180)), np.array((180, 20, 240)))
# Range 3: mid grey
mask_mid = cv2.inRange(hsv, np.array((0, 0, 100)), np.array((180, 20, 180)))

def hough(mask, p2, label):
    blurred = cv2.GaussianBlur(mask, (5, 5), 1)
    c = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                         param1=80, param2=p2, minRadius=10, maxRadius=18)
    n = 0 if c is None else len(c[0])
    print(f"  {label}: {n}")

print("Strict grey mask (S<15):")
for p2 in [15, 18, 20, 22, 25]:
    hough(mask_strict_grey, p2, f"  p2={p2}")

print("Pure grey (S<10):")
for p2 in [18, 20, 22, 25]:
    hough(mask_pure, p2, f"  p2={p2}")

print("Light grey (V>=180):")
for p2 in [18, 20, 22, 25]:
    hough(mask_light, p2, f"  p2={p2}")

print("Mid grey (V 100-180):")
for p2 in [18, 20, 22, 25]:
    hough(mask_mid, p2, f"  p2={p2}")

# Combined
print("Combinations:")
for p2 in [18, 20, 22]:
    combined = cv2.bitwise_or(cv2.bitwise_or(mask_pure, mask_light), mask_mid)
    hough(combined, p2, f"  pure+light+mid p2={p2}")
    comb2 = cv2.bitwise_or(mask_strict_grey, mask_light)
    hough(comb2, p2, f"  strict+light p2={p2}")
