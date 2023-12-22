#----------------------------------------------------------------------
# prefill_utils.py
# Author: Indu Panigrahi
#
# This file contains the implementation for prefilling pixels using 
# k-means along with useful functions for dealing with superpixels.
# The two public functions that should be used are prefill_pixels 
# and merge_superpixels
#----------------------------------------------------------------------

# imports
from skimage.segmentation import slic
from skimage.segmentation import mark_boundaries
from skimage.util import img_as_float
from skimage import io
# import matplotlib.pyplot as plt
import cv2
import numpy as np
# import matplotlib
from sklearn.cluster import KMeans
import networkx as nx
import urllib.request 
from PIL import Image 

#----------------------------------------------------------------------
'''
This function is a private helper function that generates a vector 
representation for each superpixel. Specifically, each superpixel is 
represented by the mean RGB vector of the pixels it contains. In this 
file, these vectors are clustered using k-means.
Parameters:
	img (numpy.ndarray): input image, usually read in with cv2.imread
	segments (numpy.ndarray): SLIC output, same dimensions as image
Returns:
	numpy.ndarray of size (number of superpixels, 3)
	Each row represents a superpixel with its mean RGB vector.
'''
def _suppixel_rep(img, segments):
	suppixels = np.unique(segments)
	suppixels_vectors = np.zeros((suppixels.shape[0],3))

	# For each superpixel
	for i,suppixel in enumerate(suppixels):
		# Take the mean of the RGB values of the pixels in the superpixel
		suppixel_loc = (segments == suppixel)
		rgb_vectors = img[suppixel_loc, :]
		mean_vector = np.mean(rgb_vectors, axis=0)

		# Assign the mean vector to the superpixel
		suppixels_vectors[i,:] = mean_vector

	return suppixels_vectors


#----------------------------------------------------------------------
'''
This function is a private helper function that gets the polygon 
coordinates of each superpixel.
Parameters:
	segments (numpy.ndarray of ints): SLIC output
Returns:
	list of numpy.ndarray's
	Each item in the list is a 2-dimensional numpy.ndarray.
	Each numpy.ndarray has dimensions equal to (# of polygon points, 2) 
	because it stores the coordinates of a superpixel in the 
	form [[x1, y1], [x2, y2], ...].
'''
def _get_suppixel_coords(segments):
	suppixel_coords = [] # Stores the polygon coordinates for each superpixel

	# Loop to generate polygon coordinates for each superpixel
	unique_labels = np.unique(segments)
	for i in range(len(unique_labels)):
		# Create a mask for the current superpixel
		mask = (segments == unique_labels[i]).astype(np.uint8)

		# Find the contour of the superpixel from the mask
		contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

		# Extract the contour coordinates and append them to the list
		if len(contours) > 0:
			contour = contours[0]  # Assuming there's only one contour for the superpixel
			coordinates = contour.squeeze(axis=1)  # Remove extra dimension
			suppixel_coords.append(coordinates)
		# 	coords = [] # list of cords to hold individual coordinates (represented as list of lists)
		# 	for c in coordinates:
		# 		coords.append(c.tolist())
		# 	suppixel_coords.append(list(coords))
		# 	if i == 1:
		# 		print(coordinates)
		# 		print('coords type:', type(suppixel_coords[0]))
		# 		print('coord type:', type(coords[0]))
		# # print("suppix_cords: ", suppixel_coords)

	return suppixel_coords


#----------------------------------------------------------------------
'''
This function is a private helper function that builds a graph to 
identify sets of neighboring superpixels with the same k-means labels 
(i.e. identify connected components). In this file, this function is 
used for merging neighboring superpixels with the same k-means label.
Parameters:
	img (numpy.ndarray): input image, usually read in with cv2.imread
	kmeans_labels (numpy.ndarray): numpy.ndarray of length equal 
		to num_suppixels, contains the k-means label (ints that range 
		from 0 to k-1) for each superpixel
	segments (numpy.ndarray of ints): SLIC output, same size as 
		input image
Returns:
	list
	Each item in the list represents a connected component.
	See NetworkX documentation for more information.
'''
def _get_connected_components(img, kmeans_labels, segments):
	# Map superpixel labels to their corresponding k-means labels
	superpixel_to_kmeans = {label: kmeans_label for label, kmeans_label in zip(np.unique(segments), kmeans_labels)}

	# Create a graph to represent adjacency between superpixels with the same k-means label
	adjacency_graph = nx.Graph()

	# Iterate through the image pixels
	for y in range(img.shape[0]):
		for x in range(img.shape[1]):
			current_label = segments[y, x]
			current_kmeans_label = superpixel_to_kmeans[current_label]

			# Check the adjacent superpixels (up, down, left, right)
			neighbors = [(y-1, x), (y+1, x), (y, x-1), (y, x+1)]
			for neighbor_y, neighbor_x in neighbors:
				if 0 <= neighbor_y < img.shape[0] and 0 <= neighbor_x < img.shape[1]:
					neighbor_label = segments[neighbor_y, neighbor_x]
					neighbor_kmeans_label = superpixel_to_kmeans[neighbor_label]

					# Add edges to the graph for adjacent superpixels with the same k-means label
					if neighbor_kmeans_label == current_kmeans_label:
						adjacency_graph.add_edge(current_label, neighbor_label)

	connected_components = list(nx.connected_components(adjacency_graph))
	return connected_components


#----------------------------------------------------------------------
'''
This function pre-labels the pixels in an image using superpixels and 
the k-means algorithm.
Example Usage:
	coords, kmeans_labels, segments = prefill_pixels(img_path, 100, 7)
Parameters:
	img_path (str): path to image file (e.g. "labrador_r02104540.tif")
	num_suppixels (int): desired number of superpixels
	k (int): desired number of clusters
Returns:
	suppixel_coords (list of numpy.ndarray's): see comment for what the
		_get_suppixel_coords function returns
	kmeans_labels (numpy.ndarray): numpy.ndarray of length equal 
		to num_suppixels, contains the k-means label (ints that range 
		from 0 to k-1) for each superpixel
	segments (numpy.ndarray of ints): SLIC output, same size as 
		input image
'''
''' Draw the superpixels with this output and color them according to the k-means category'''

def prefill_pixels(img_path, num_suppixels, k):
	urllib.request.urlretrieve(img_path, "image") 
	
	img = np.asarray(Image.open("image"))
	# img = cv2.imread(img_path)
	
	# Note: values of segments are 1 through number of superpixels made
	# Get vector representations for superpixels
	segments = slic(img, n_segments=num_suppixels, sigma=2)
	suppixels = _suppixel_rep(img, segments)


	# Run k-means to cluster the vector representations
	try: 
		kmeans_labels = KMeans(n_clusters=k, n_init=15).fit_predict(suppixels)

		# Get polygon coordinates of the superpixels
		suppixel_coords = _get_suppixel_coords(segments)
		for suppix in suppixel_coords:
			suppix = list(suppix)

		return [0, [suppixel_coords, kmeans_labels, segments]]
	
	except Exception as ex:
		return [1, ex]





#----------------------------------------------------------------------
'''
This function merges neighboring superpixels that have the same k-means 
label together. 
IMPORTANT: This function assumes that you set the k-means label of the 
superpixels that the user wants to remove to -1.
Example Usage:
	new_coords, new_labels, new_segments = merge_superpixels(img_path, kmeans_labels, segments)
Parameters:
	img_path (str): path to image file (e.g. "labrador_r02104540.tif")
	kmeans_labels (numpy.ndarray): numpy.ndarray of length equal 
		to num_suppixels, contains the k-means label (ints that range 
		from 0 to k-1) for each superpixel
	segments (numpy.ndarray of ints): SLIC output, same size as 
		input image
Returns:
	filtered_coords (list of numpy.ndarray's): see comment for what the
		_get_suppixel_coords function returns
	merged_kmeans_labels (numpy.ndarray): numpy.ndarray of length equal 
		to the number of merged regions, contains the k-means label 
		(ints that range from 0 to k-1) for each merged region
	merged_segments (numpy.ndarray of ints): SLIC output updated to be 
		consistent with the merged regions, same size as input image
'''

'''Call merge super pixels on coordinates that are still there'''
def merge_superpixels(img_path, kmeans_labels, segments):
	urllib.request.urlretrieve(img_path, "image") 
	img = np.array(Image.open("image"))
	# img = cv2.imread(img_path)

	# Identify groups of neighboring superpixels that have the same k-means label
	connected_components = _get_connected_components(img, kmeans_labels, segments)

	# Create a mapping from old labels to new labels after merging
	label_mapping = {}

	for component in connected_components:
		if len(component) > 1:
			# Merge superpixels within the same connected component
			new_label = min(component) # Chose to use the min label
			for label in component:
				label_mapping[label] = new_label

	# Create an image-sized array of merged labels
	merged_segments = np.copy(segments)
	for old_label, new_label in label_mapping.items():
		merged_segments[merged_segments == old_label] = new_label

	# Get coordinates of merged superpixels
	merged_coords = _get_suppixel_coords(merged_segments)

	# Remove superpixels that the user decided to remove
	merged_kmeans_labels = []
	filtered_coords = []
	for i in range(len(merged_coords)):
		kmeans_label = kmeans_labels[i]
		if kmeans_label != -1:
			merged_kmeans_labels.append(kmeans_label)
			filtered_coords.append(merged_coords[i])
	merged_kmeans_labels = np.array(merged_kmeans_labels)

	return filtered_coords, merged_kmeans_labels, merged_segments