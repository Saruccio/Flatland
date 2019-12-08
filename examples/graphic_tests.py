import matplotlib.pyplot as plt
import numpy as np


def f(t):
    return np.exp(-t) * np.cos(2*np.pi*t)

t1 = np.arange(0.0, 5.0, 0.1)
t2 = np.arange(0.0, 5.0, 0.02)

plt.figure()
left = 121
plt.subplot(left)
plt.plot(t1, f(t1), 'bo', t2, f(t2), 'k')

right = 122
plt.subplot(right)
plt.plot(t2, np.cos(2*np.pi*t2), 'r--')
plt.show()
