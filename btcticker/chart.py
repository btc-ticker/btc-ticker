from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import numpy as np
from PIL import Image


def makeSpark(pricestack, figsize=(10, 3), dpi=17):
    # Draw and save the sparkline that represents historical data

    # Subtract the mean from the sparkline to make the mean appear on the plot (it's really the x axis)    
    x = pricestack-np.mean(pricestack)


    fig = Figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot()
    canvas = FigureCanvasAgg(fig)
    ax.plot(x, color='k', linewidth=6)
    ax.plot(len(x)-1, x[-1], color='r', marker='o')

    # Remove the Y axis
    for k,v in ax.spines.items():
        v.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axhline(c='k', linewidth=4, linestyle=(0, (5, 2, 1, 2)))
    canvas.draw()
    buf = canvas.buffer_rgba()
    X = np.asarray(buf)
    im = Image.fromarray(X)
    
    return im
