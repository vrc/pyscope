#!/usr/bin/python3

import math
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(-math.pi, math.pi, 2000)
y = [math.sin(v) for v in x]

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
ax.plot(x/math.pi, y)
ax.grid(True)
plt.show()
