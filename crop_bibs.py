from PIL import Image
import matplotlib.pyplot as plt

# Load the image
img_path = "IMG_6401-X2.jpg"
image = Image.open(img_path)

# Convert to displayable format
fig, ax = plt.subplots()
ax.imshow(image)
coords = []

def on_click(event):
    if event.xdata and event.ydata:
        coords.append((int(event.xdata), int(event.ydata)))
        print(f"Clicked at: ({int(event.xdata)}, {int(event.ydata)})")
        if len(coords) == 2:
            # Draw rectangle
            x0, y0 = coords[0]
            x1, y1 = coords[1]
            cropped = image.crop((x0, y0, x1, y1))
            fname = input("Save as filename (e.g., bib_left.jpg): ")
            cropped.save(fname)
            print(f"✅ Saved {fname}")
            coords.clear()

cid = fig.canvas.mpl_connect('button_press_event', on_click)
plt.title("Click two corners of the bib area")
plt.show()
