import os
import logging
import pickle
import tensorflow as tf
import numpy as np
import siamese_network as network
import sampling as sampling
from parameters import LEARN_RATE, EPOCHS, CHECKPOINT_EVERY, BATCH_SIZE
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import random

def get_one_hot_similarity_label(left_labels, right_labels):
    sim_labels = []
    sim_labels_num = []
    for i in range(0,len(left_labels)):
        if left_labels[i] == right_labels[i]:
            sim_labels.append([0.0,1.0])
            sim_labels_num.append(1)
        else:
            sim_labels.append([1.0,0.0])
            sim_labels_num.append(0)
    return sim_labels, sim_labels_num


def train_model(logdir, left_inputs, right_inputs, embedfile, epochs=EPOCHS):
    """Train a classifier to label ASTs"""


    n_classess = 2
    with open(left_inputs, 'rb') as fh:
        _, left_trees, left_algo_labels = pickle.load(fh)


    with open(right_inputs, 'rb') as fh:
        _, right_trees, right_algo_labels = pickle.load(fh)

    with open(embedfile, 'rb') as fh:
        embeddings, embed_lookup = pickle.load(fh)
        num_feats = len(embeddings[0])


    # build the inputs and outputs of the network
    left_nodes_node, left_children_node, left_pooling_node = network.init_net_for_siamese(
        num_feats
    )

    right_nodes_node, right_children_node, right_pooling_node = network.init_net_for_siamese(
        num_feats
    )

    merge_node = tf.concat([left_pooling_node, right_pooling_node], -1)


    hidden_node = network.hidden_layer(merge_node, 200, n_classess)


    out_node = network.out_layer(hidden_node)

    labels_node, loss_node = network.loss_layer(hidden_node, n_classess)

    optimizer = tf.train.AdamOptimizer(LEARN_RATE)
    train_step = optimizer.minimize(loss_node)

    # tf.summary.scalar('loss', loss_node)

    ### init the graph
    sess = tf.Session()#config=tf.ConfigProto(device_count={'GPU':0}))
    sess.run(tf.global_variables_initializer())

    
    steps = 0

    print "Preparing data..."
    temp_zip = sampling.produce_train_pairwise_data(left_trees,right_trees)

    print "Finish prepraring....."
    for epoch in range(1, epochs+1):
        random.shuffle(temp_zip)
        shuffle_left_trees, shuffle_right_trees = zip(*temp_zip)
        for left_gen_batch, right_gen_batch in sampling.batch_siamese_random_samples(shuffle_left_trees, left_algo_labels, shuffle_right_trees, right_algo_labels, embeddings, embed_lookup, BATCH_SIZE):
            
            left_nodes, left_children, left_labels_one_hot, left_labels = left_gen_batch

            right_nodes, right_children, right_labels_one_hot, right_labels = right_gen_batch

            sim_labels, sim_labels_num = get_one_hot_similarity_label(left_labels,right_labels)

            hidden = sess.run(
                [hidden_node],
                feed_dict={
                    left_nodes_node: left_nodes,
                    left_children_node: left_children,
                    right_nodes_node: right_nodes,
                    right_children_node: right_children,
                    labels_node: sim_labels
                }
            )
            

            print("Hidden:",hidden,"True labels one hot:",sim_labels)
          
    
            steps+=1
        steps = 0
  
   
def main():
    logdir = "./tbcnn/logs/4"
    cpp_inputs = "./data/cpp_algorithms_trees.pkl"

    java_inputs = "./data/java_algorithms_trees.pkl"

    embeddings = "./data/fast_pretrained_vectors.pkl"



    train_model(logdir,cpp_inputs, java_inputs, embeddings) 


if __name__ == "__main__":
    main()