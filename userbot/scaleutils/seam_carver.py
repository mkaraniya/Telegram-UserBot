import numpy as np
from numba import njit
from numba.types import int64
from tqdm import trange


def dual_gradient_energy(x_0, x_1, y_0, y_1):
    """Suggested from
    http://www.cs.princeton.edu/courses/archive/spring14/cos226/assignments/seamCarving.html

    :params
        The east/west/north/south neighbors of the pixel whose energy to calculate.
        Each is an len-3 array [r,g,b]
    :returns float
        dual gradient energy at the pixel with those neighbors
    """
    return sum(pow((x_0-x_1), 2) + pow((y_0-y_1), 2))


def energy_map(img):
    """
    Parameters
    ==========

    img: numpy.array with shape (height, width, 3)
    func: function
        The energy function to use. Should take in 4 pixels and return a float.

    :returns 2-D numpy array with the same height and width as img
        Each energy[x][y] is an int specifying the energy of that pixel
    """
    x_0 = np.roll(img, -1, axis=1).T
    x_1 = np.roll(img, 1, axis=1).T
    y_0 = np.roll(img, -1, axis=0).T
    y_1 = np.roll(img, 1, axis=0).T

    # we do a lot of transposing before and after here because sums in the
    # energy function happen along the first dimension by default when we
    # want them to be happening along the last (summing the colors)
    en_map = dual_gradient_energy(x_0, x_1, y_0, y_1).T
    return en_map


@njit(nogil=True, cache=True)
def cumulative_energy(energy):
    """
    https://en.wikipedia.org/wiki/Seam_carving#Dynamic_programming

    Parameters
    ==========
    energy: 2-D numpy.array(uint8)
        Produced by energy_map

    Returns
    =======
        tuple of 2 2-D numpy.array(int64) with shape (height, width).
        paths has the x-offset of the previous seam element for each pixel.
        path_energies has the cumulative energy at each pixel.
    """
    height, width = energy.shape
    paths = np.zeros((height, width), dtype=int64)
    path_energies = np.zeros((height, width), dtype=int64)
    path_energies[0] = energy[0]
    paths[0] = np.arange(width) * np.nan

    for i in range(1, height):
        for j in range(width):
            # Note that indexing past the right edge of a row, as will happen if j == width-1, will
            # simply return the part of the slice that exists
            prev_energies = path_energies[i-1, max(j-1, 0):j+2]
            least_energy = prev_energies.min()
            path_energies[i][j] = energy[i][j] + least_energy
            paths[i][j] = np.where(prev_energies == least_energy)[0][0] - (1*(j != 0))

    return paths, path_energies


@njit(nogil=True, cache=True)
def seam_end(energy_totals):
    """
    Parameters
    ==========
    energy_totals: 2-D numpy.array(int64)
        Cumulative energy of each pixel in the image

    Returns
    =======
        numpy.int64
        the x-coordinate of the bottom of the seam for the image with these
        cumulative energies
    """
    return list(energy_totals[-1]).index(min(energy_totals[-1]))


@njit(nogil=True, cache=True)
def find_seam(paths, end_x):
    """
    Parameters
    ==========
    paths: 2-D numpy.array(int64)
        Output of cumulative_energy_map. Each element of the matrix is the offset of the index to
        the previous pixel in the seam
    end_x: int
        The x-coordinate of the end of the seam

    Returns
    =======
        1-D numpy.array(int64) with length == height of the image
        Each element is the x-coordinate of the pixel to be removed at that y-coordinate. e.g.
        [4,4,3,2] means "remove pixels (0,4), (1,4), (2,3), and (3,2)"
    """
    height, _ = paths.shape[:2]
    seam = [end_x]

    for i in range(height-1, 0, -1):
        cur_x = seam[-1]
        offset_of_prev_x = paths[i][cur_x]
        seam.append(cur_x + offset_of_prev_x)

    seam.reverse()
    return seam


def remove_seam(img, seam):
    """
    Parameters
    ==========
    img: 3-D numpy.array
        RGB image you want to resize
    seam: 1-D numpy.array
        seam to remove. Output of seam function

    Returns
    =======
        3-D numpy array of the image that is 1 pixel shorter in width than the input img
    """
    height, _ = img.shape[:2]
    return np.array([np.delete(img[row], seam[row], axis=0) for row in range(height)])


def resize_image(full_img, cropped_pixels):
    """
    Parameters
    ==========
    full_img: 3-D numpy.array
        Image you want to crop.
    cropped_pixels: int
        Number of pixels you want to shave off the width. Aka how many vertical seams to remove.

    Returns
    =======
        3-D numpy array of your now cropped_pixels-slimmer image.
    """
    img = full_img.copy()

    for _ in trange(cropped_pixels, desc='cropping image by {0} pixels'.format(cropped_pixels)):
        e_map = energy_map(img)
        e_paths, e_totals = cumulative_energy(e_map)
        seam = find_seam(e_paths, seam_end(e_totals))
        img = remove_seam(img, seam)

    return img