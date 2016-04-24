import numpy as np
import math
import csv
import random
from sklearn.datasets.samples_generator import make_blobs
import config
import pickle
import os
import config
import shutil
import sys
import math


def AddMolecularData(all_clusters, number_of_active_molecules, number_of_inactive_molecules, 
    diversity_threshold, purity_threshold, num_diverse_pure_clusters, DATA_DIRECTORY, clustered_dimension_array,
    points_per_cluster, diversity_percentage = False, difficult_version = False):
    "Vast method that strives to make our generated clustering data as realistic as possible to real \
    molecular data. This entails adding details about various details about the molecular feature space."

    if diversity_percentage:
        diversity_threshold = int(diversity_threshold * number_of_active_molecules)
    current_diverse_pure_clusters = 0
    
    # Prevent parameter combinations that may lead to severe errors
    if (num_diverse_pure_clusters > len(all_clusters)):
            raise ValueError("Current num_diverse_clusters is greater than the actual number of existing clusters provided")
    
    actives_fragments_to_molecule_mapping = {}
    inactives_fragments_to_molecule_mapping = {}
    
    with open(os.path.join(DATA_DIRECTORY,"generated_test_clusters.pkl"),'w+') as f_handle:

        # Keep track of all metadata for future tests
        generated_clusters = {}
        generated_clusters["clusters"] = []
        generated_clusters["num_clusters"] = len(all_clusters)
        generated_clusters["centroids"] = []
        generated_clusters["cluster_radii"] = []
        generated_clusters["num_active_molecules"] = number_of_active_molecules
        generated_clusters["num_inactive_molecules"] = number_of_inactive_molecules
        generated_clusters["diversity"] = diversity_threshold
        generated_clusters["purity"] = purity_threshold
        generated_clusters["num_diverse_pure_clusters"] = num_diverse_pure_clusters
        generated_clusters["significant_clusters"] = []
        generated_clusters["cluster_subspace_dimensions"] = clustered_dimension_array
        generated_clusters["points_per_cluster"] = points_per_cluster
        counter = 0
        
        for cluster in all_clusters:
            already_assigned_fragments = []
            num_points = len(cluster)
            generated_clusters["clusters"].append([])
            centroid = [0] * len(cluster[0][1:])
            min_vals = cluster[0][1:]
            max_vals = cluster[0][1:]

            if current_diverse_pure_clusters < num_diverse_pure_clusters:
                # First deal with diversity
                # Up to the user to make sure that each test cluster has enough points to
                # even be able to be considered diverse.
                max_fragments = np.min([num_points, diversity_threshold])
                for i in range(max_fragments):
                    actives_fragments_to_molecule_mapping[cluster[i][0]] = [i % number_of_active_molecules]
                    already_assigned_fragments.append(i)
                    generated_clusters["clusters"][counter].append(cluster[i][0])
                    centroid+=cluster[i][1:]
                    min_vals = np.minimum(min_vals,cluster[i][1:])
                    max_vals = np.maximum(max_vals,cluster[i][1:])
            
                # Then deal with purity
                number_of_active_fragments_needed = int(np.ceil(purity_threshold * num_points))
                for i in range(number_of_active_fragments_needed):
                    if i not in already_assigned_fragments:
                        actives_fragments_to_molecule_mapping[cluster[i][0]] = [i % number_of_active_molecules]
                        already_assigned_fragments.append(i)
                        generated_clusters["clusters"][counter].append(cluster[i][0])
                        centroid+=cluster[i][1:]
                        min_vals = np.minimum(min_vals,cluster[i][1:])
                        max_vals = np.maximum(max_vals,cluster[i][1:])

                # Assign the rest to inactives
                for i in range(max_fragments,num_points):
                    if i not in already_assigned_fragments:
                        inactives_fragments_to_molecule_mapping[cluster[i][0]] = [i % number_of_inactive_molecules]
                        generated_clusters["clusters"][counter].append(cluster[i][0])
                        centroid+=cluster[i][1:]
                        min_vals = np.minimum(min_vals,cluster[i][1:])
                        max_vals = np.maximum(max_vals,cluster[i][1:])


                current_diverse_pure_clusters+=1
                generated_clusters["significant_clusters"].append(counter)
        
            else:
                # In difficult version the rest of the clusters all have only inactive fragments
                if difficult_version:
                    for i in range(num_points):
                        # Choose an inactive molecule at random, doesn't matter which one
                        inactives_fragments_to_molecule_mapping[cluster[i][0]] = [i % number_of_inactive_molecules]
                        generated_clusters["clusters"][counter].append(cluster[i][0])
                        centroid+=cluster[i][1:]
                        min_vals = np.minimum(min_vals,cluster[i][1:])
                        max_vals = np.maximum(max_vals,cluster[i][1:])
            
                # Else in the easy version assign each cluster to actives or inactives randomly
                else:
                    active = np.random.randint(2)
                    if active:
                        for i in range(num_points):
                            # Choose an active molecule at random, doesn't matter which one
                            actives_fragments_to_molecule_mapping[cluster[i][0]] = [i % number_of_active_molecules]
                            generated_clusters["clusters"][counter].append(cluster[i][0])
                            centroid+=cluster[i][1:]
                            min_vals = np.minimum(min_vals,cluster[i][1:])
                            max_vals = np.maximum(max_vals,cluster[i][1:])
                    else:
                        for i in range(num_points):
                            # Choose an inactive molecule at random, doesn't matter which one
                            inactives_fragments_to_molecule_mapping[cluster[i][0]] = [i % number_of_inactive_molecules]
                            generated_clusters["clusters"][counter].append(cluster[i][0])
                            centroid+=cluster[i][1:]
                            min_vals = np.minimum(min_vals,cluster[i][1:])
                            max_vals = np.maximum(max_vals,cluster[i][1:])

            centroid/=num_points
            cluster_radius = 0
            for i in range(len(min_vals)):
                if clustered_dimension_array[counter][0,i] == 1:
                    max_distance = np.maximum(np.absolute(centroid[i] - min_vals[i]),np.absolute(centroid[i]-max_vals[i]))
                    cluster_radius+=max_distance**2
            cluter_radius = np.sqrt(cluster_radius) 

            generated_clusters["cluster_extreme_values"] = {"min":min_vals,"max":max_vals}
            generated_clusters["cluster_radii"].append(cluster_radius)
            generated_clusters["centroids"].append(centroid)
            counter+=1

        pickle.dump(generated_clusters,f_handle,pickle.HIGHEST_PROTOCOL)
    
    with open(os.path.join(DATA_DIRECTORY,"test_actives_fragment_molecule_mapping.pkl"),'wb+') as f_handle:
         pickle.dump(actives_fragments_to_molecule_mapping, f_handle, pickle.HIGHEST_PROTOCOL)
    
    with open(os.path.join(DATA_DIRECTORY,"test_inactives_fragment_molecule_mapping.pkl"),'wb+') as f_handle:
        pickle.dump(inactives_fragments_to_molecule_mapping, f_handle, pickle.HIGHEST_PROTOCOL)

def FlushData(clusters, DATA_DIRECTORY):
    "Method for flushing the generated clusters to a file. This file will be located in DATA_DIRECTORY"
    # Create new file
    open(os.path.join(DATA_DIRECTORY,"test_molecular_feature_matrix.csv"), 'w+')
    with open(os.path.join(DATA_DIRECTORY,"test_molecular_feature_matrix.csv"), 'a') as f_handle:
        for cluster in clusters:
            # Flush everything except the identification key
            new_cluster = np.delete(cluster, 0, 1)
            np.savetxt(f_handle, new_cluster, delimiter=",", fmt="%f")


def LabelDataWithKeys(clusters):
    "This method lables the raw data points of clusters with identification keys. This will help \
    in idenitfying the points in each cluster when evaluating subspace clustering algorithm results."

    labelled_clusters = []
    counter = 0

    for i in range(clusters.shape[0]):
        current_cluster = clusters[i]
        new_cluster = np.empty([current_cluster.shape[0],current_cluster.shape[1]+1],dtype=np.float)

        for j in range(current_cluster.shape[0]):
            current_vector = current_cluster[j]
            # Insert an identification key
            new_vector = np.insert(current_vector,0,counter)
            # new_cluster.append(new_vector)
            new_cluster[j] = new_vector
            counter = counter +1

        labelled_clusters.append(new_cluster)

    return np.asarray(labelled_clusters)

def checkIntersection(cluster_seed_one,cluster_seed_two,radius):
    "Checks whether the first cluster center and the second cluster center intersect. \
    We define intersect to mean dist(cluster_seed_one[i],cluster_seed_two[i]) <= 2*radius \
    for any i = 0,...,num_clustered_dimensions"
    
    # centroid_distance = np.linalg.norm(np.subtract(cluster_seed_one,cluster_seed_two))
    # if centroid_distance <= 2*radius:
    #     return True

    # return False
    
    if (np.absolute(np.array(cluster_seed_one) - np.array(cluster_seed_two)) > 2*radius).any():
        return False

    return True



def GenerateSeveralClusters(value_range, num_clusters, number_of_points, intercluster_distance, 
    density, num_clustered_dimensions, total_number_dimensions):
    "Main cluster generation module. value_range specifies the range of the values taken by the clusters. \
    num_clusters is the number of clusters to be generated. \
    number_of_points is the number of points per cluster. \
    inter_cluster distance is the minimum distance between in one dimension between any two \
    centroids of the generated clusters. \
    density is the radius of the cluster. \
    num_clustered_dimensions is the number of clustered subspace dimensions. \
    total_number_dimensions is the total number of dimensions (clustered and unclustered dimensions)."
    
    clusters = []
    # Keep track of the center seeds of the clusters - in other words, the centroids.
    cluster_seeds = []
    # Keep track of dimensionality of subspace clusters.
    clustered_dimensions_array = []
    # The vector corresponding to the density in each dimension of the clusters, will be used to 
    # compute the radius using the vector norm
    deviation_vector = np.empty(num_clustered_dimensions,dtype=float)
    deviation_vector.fill(density)
    # Compute radius using the vector norm
    cluster_radius = math.sqrt(deviation_vector.dot(deviation_vector))

    while(len(clusters)!=num_clusters):
        # First seed will ge generated at the origin.
        if(len(clusters) == 0):
            current_center_seed = [0] * total_number_dimensions
            temporary_seed = []
            # Shuffle the seed's dimensions so that we have some variety
            random_permutation = np.random.permutation(np.arange(total_number_dimensions))
            PerformPermutationMapping(current_center_seed,temporary_seed,random_permutation)
            # Initialize a dictionary that keeps track of how we map the dimensions
            dimension_mapping = {index:val for index,val in enumerate(random_permutation)}
        else:
            # Try and shift the old center seed to obtain a new center seed
            for i in range(num_clustered_dimensions):
                current_center_seed[i] += intercluster_distance
                temporary_seed = []
                # Shuffle the seed's dimensions so that we have some variety
                random_permutation = np.random.permutation(np.arange(total_number_dimensions))
                PerformPermutationMapping(current_center_seed,temporary_seed,random_permutation)
                # Initialize a dictionary that keeps track of how we map the dimensions
                dimension_mapping = {index:val for index,val in enumerate(random_permutation)}
                # Check if the newly generated seed intersects with any prior generated seeds.
                intersects = False
                for old_cluster_seed in cluster_seeds:
                    # Check intersections with prior seeds
                    if checkIntersection(temporary_seed,old_cluster_seed,density):
                        intersects = True
                        break
                
                # We found a non-intersecting seed
                if not intersects:
                    # Also need to make sure that we are still in the value range
                    if (np.array(temporary_seed) <= value_range).all():
                        break
                # We've tried adding the intercluster_distance to all dimensions and still get 
                # intersections, therefore we notify the user
                if i==num_clustered_dimensions-1:
                    raise ValueError('Current parameters lead to intersecting clusters, please input different parameters')
        
        # Keep track of the clustered dimensions metadata
        clustered_dimensions = np.empty([1,total_number_dimensions]).reshape(1,total_number_dimensions)
        for key,val in dimension_mapping.iteritems():
            if val < num_clustered_dimensions:
                clustered_dimensions[0,key] = 1
            else:
                clustered_dimensions[0,key] = 0
        
        clustered_dimensions_array.append(clustered_dimensions)
        cluster_seeds.append(temporary_seed)

        # Get the vectors of the subspace cluster, taken from a Guassian blob distribution with the mean
        # as the cluster centroid. Note that we use the six-sigma principle in order to generate a 
        # reasonable standard deviation parameter.
        clustered_vectors, labels_true = make_blobs(n_samples=number_of_points, centers=current_center_seed[0:num_clustered_dimensions],
            cluster_std=density/6, random_state=1)

        # Initialize a new cluster - in all the dimensions.
        cluster = np.empty([number_of_points,total_number_dimensions],dtype=np.float)

        # Fill in the unclustered dimensions of the generated vectors, and append to our created cluster
        for i in range(number_of_points):
            # Create new vector, with all the dimensions
            new_vector = np.empty([1,total_number_dimensions],dtype=np.float).reshape(1,total_number_dimensions)
            # Fill in the clustered dimensions
            for j in range(num_clustered_dimensions):
                new_vector[0,j] = clustered_vectors[i,j]
            # Fill in the unclustered dimensions
            for j in range(num_clustered_dimensions,total_number_dimensions):
                new_vector[0,j] = np.random.uniform(0,value_range)
            # Rearrange the dimensions according to our random permutation
            temp_vector = np.copy(new_vector)
            for j in range(total_number_dimensions):
                new_vector[0,j] = temp_vector[0,dimension_mapping[j]]
            # Finally, add the vector to our cluster
            cluster[i] = new_vector
      
        clusters.append(cluster)

    return [np.asarray(clusters),clustered_dimensions_array]


def PerformPermutationMapping(arr,newarr,permutation):
    "Performs a mapping of arr into newarr according to the permutation parameter"
    for j in range(len(arr)):
        newarr.append(arr[permutation[j]])

# python generate_clusters.py 50 10 5 1 3 10 20 5 ../TestFragmentDescriptorData/1
# python generate_clusters.py 250 10 25 5 10 50 20 5 ../TestFragmentDescriptorData/1
def main():
    "Generates various test subspace clusters according to the input parameters \
    Parameters:  range, points_per_cluster, ICD, density, num_clustered_dimensions,\
     total_number_dimensions,num_active_molecules,amount_of_clusters,DATA_DIRECTORY"

    # Range of cluster space (range in each dimension)
    ambient_space_range = float(sys.argv[1])
    # Decide amount of clusters 
    amount_of_clusters = int(sys.argv[8])
    # Points per cluster -> constant accross all clusters
    amount_of_points = int(sys.argv[2])
    # The minimum distance between two sequentially generated clusters
    intercluster_distance = float(sys.argv[3])
    # Density - the range in each dimension of the clusters
    density_per_dimension = float(sys.argv[4])
    # Number of clustered dimensions
    num_clustered_dimensions = int(sys.argv[5])
    # Total number of dimensions
    total_number_dimensions = int(sys.argv[6])
    # Purity of the cluster; that is, purity = .95 ==> 95% of the cluster's points are pure,
    # and the rest are some noise points that don't really belong in the cluster
    # Will add extra serendipity to our clustering and we will keep it constant
    # purity = 1.0

    clusters,clustered_dimension_array = GenerateSeveralClusters(ambient_space_range,amount_of_clusters,amount_of_points,intercluster_distance,\
        density_per_dimension,num_clustered_dimensions,total_number_dimensions)
    
    # Label the data points in our clusters with identification keys
    labelled_clusters = LabelDataWithKeys(clusters)
    
    # Flush the labelled clusters
    FlushData(labelled_clusters, sys.argv[9])
    
    num_active_molecules = int(float(sys.argv[7]))
    num_inactive_molecules = 100 - num_active_molecules
    # Add molecular data with values for purity, diversity, etc. 
    data_with_classes = AddMolecularData(labelled_clusters, num_active_molecules, num_inactive_molecules, 7, .6, 2, sys.argv[9], clustered_dimension_array, amount_of_points, diversity_percentage=False,difficult_version=True)

if __name__ == '__main__':
    main()
