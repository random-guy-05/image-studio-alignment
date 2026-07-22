import cv2, numpy as np
img = cv2.imread("/tmp/v3.png")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
blue_mask = cv2.inRange(hsv, np.array((100, 120, 100)), np.array((130, 255, 255)))

# All rows with any blue
row_blue = blue_mask.sum(axis=1) / 255
significant = np.where(row_blue > 20)[0]
print(f"Rows with >20 blue: {len(significant)}")
# Group consecutive
if len(significant) > 0:
    groups = [[significant[0]]]
    for r in significant[1:]:
        if r - groups[-1][-1] <= 3:
            groups[-1].append(r)
        else:
            groups.append([r])
    print(f"Groups: {len(groups)}")
    for g in groups:
        print(f"  rows {g[0]}-{g[-1]}  (width {g[-1]-g[0]+1})  max_blue_in_group={int(row_blue[g[0]:g[-1]+1].max())}")

# Also check grey
grey_light = cv2.inRange(hsv, np.array((0, 0, 180)), np.array((180, 20, 240)))
grey_black = cv2.inRange(hsv, np.array((0, 0, 0)),   np.array((180, 60,  60)))
print(f"\nlight grey pixels: {int((grey_light>0).sum())}")
print(f"black pixels: {int((grey_black>0).sum())}")
