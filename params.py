""" Use to generate model config files """

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import argparse

# Image parameters
DATA_PATH = '/mindhive/dicarlolab/common/imagenet/data.raw'  # openmind
# DATA_PATH = '/data/imagenet_dataset/hdf5_cached_from_om7/data.raw' # agent

IMAGE_SIZE_ORIG = 256
IMAGE_SIZE_CROP = 224  # 224
NUM_CHANNELS = 3
PIXEL_DEPTH = 255
NUM_LABELS = 1000
TOTAL_IMGS_HDF5 = 1290129

# Training parameters
TRAIN_SIZE = 1000000  # 1000000
NUM_EPOCHS = 90
BATCH_SIZE = 256  # to be split among GPUs. For train, eval

# Run configuration parameters
NUM_PREPROCESS_THREADS = 1  # per tower. should be multiple of 4
NUM_READERS = 1  # parallel readers during training
INPUT_QUEUE_MEMORY_FACTOR = 1  # size of queue of preprocessed images.
LOG_DEVICE_PLACEMENT = False

# Evaluation parameters
NUM_VALIDATION_BATCHES = 200
EVAL_BATCH_SIZE = BATCH_SIZE

# Paths for saving things
# CHECKPOINT_DIR = '/home/mrui/bypass/outputs/' # for eval to read
CHECKPOINT_DIR = '/om/user/mrui/model/outputs/'
SAVE_PATH = CHECKPOINT_DIR + 'anet1a'  # file name base.
# NOTE: if you use another directory make sure it exists first.

# use tensorboard for graph visualization. Saved to CHECKPOINT_DIR
TENSORBOARD = False

# Write training loss to file SAVE_PATH + '_loss.csv'
SAVE_LOSS = True
SAVE_LOSS_FREQ = 5  # keeps loss from every SAVE_LOSS_FREQ steps.

# Saving model parameters (variables)
SAVE_VARS = True  # save variables if True
SAVE_VARS_FREQ = 300 * 10  # how often to save vars (divisble by 10)
MAX_TO_KEEP = 10

# Restoring variables from file
RESTORE_VARS = False  # If True, restores variables from RESTORE_VAR_FILE
START_STEP = 27000  # to be used for step counter.
RESTORE_VAR_FILE = SAVE_PATH + '-' + str(START_STEP)

# loss function parameters
TIME_PENALTY = 1.2  # 'gamma' time penalty as # time steps passed increases

# Optimization parameters
GRAD_CLIP = False
LEARNING_RATE_BASE = 0.03  # .001 for Adam. initial learning rate.
LEARNING_RATE_DECAY_FACTOR = 0.85
MOMENTUM = 0.9  # for momentum optimizer
NUM_EPOCHS_PER_DECAY = 1  # exponential decay each epoch

T_TOT = 8  # Total number of time steps to run model
# Note: if all of input is  desired to be run; then T = length(input) +
# N_cells + 1. Otherwise, T >= shortest path is given and input is
# truncated to length = T - shortest_path
INITIAL_STATES = None  # dictionary of initial states for cells
INPUT_SEQ = None  # Sequence of input images. If None, just repeats input image
# Graph structure
# sizes = [batch size, spatial, spatial, depth(num_channels)]

LAYER_SIZES = {
    0: {'state': [BATCH_SIZE, IMAGE_SIZE_CROP, IMAGE_SIZE_CROP, NUM_CHANNELS],
        'output': [BATCH_SIZE, IMAGE_SIZE_CROP, IMAGE_SIZE_CROP,
                   NUM_CHANNELS]},  # input
    1: {'state': [BATCH_SIZE, IMAGE_SIZE_CROP / 4, IMAGE_SIZE_CROP / 4, 96],
        'output': [BATCH_SIZE, IMAGE_SIZE_CROP / 8, IMAGE_SIZE_CROP / 8, 96]},
    # stride2 conv AND pool!
    2: {'state': [BATCH_SIZE, IMAGE_SIZE_CROP / 8, IMAGE_SIZE_CROP / 8, 256],
        'output': [BATCH_SIZE, IMAGE_SIZE_CROP / 16, IMAGE_SIZE_CROP / 16,
                   256]},  # convpool
    3: {'state': [BATCH_SIZE, IMAGE_SIZE_CROP / 16, IMAGE_SIZE_CROP / 16, 384],
        'output': [BATCH_SIZE, IMAGE_SIZE_CROP / 16, IMAGE_SIZE_CROP / 16,
                   384]},  # conv
    4: {'state': [BATCH_SIZE, IMAGE_SIZE_CROP / 16, IMAGE_SIZE_CROP / 16, 384],
        'output': [BATCH_SIZE, IMAGE_SIZE_CROP / 16, IMAGE_SIZE_CROP / 16,
                   384]},  # conv
    5: {'state': [BATCH_SIZE, IMAGE_SIZE_CROP / 16, IMAGE_SIZE_CROP / 16, 256],
        'output': [BATCH_SIZE, IMAGE_SIZE_CROP / 32, IMAGE_SIZE_CROP / 32,
                   256]},  # convpool
    6: {'state': [BATCH_SIZE, 4096], 'output': [BATCH_SIZE, 4096]},  # fc
    7: {'state': [BATCH_SIZE, 4096], 'output': [BATCH_SIZE, 4096]},  # fc
    }
WEIGHT_DECAY = 0.0005
FC_KEEP_PROB = 0.5  # for training; config writes None for eval mode
DECAY_PARAM_INIT = None  # -1.1 initialize decay_factor t= sigmoid(-1.1) = 0.25
MEMORY = False  # just for Conv or ConvPool layers; True to use memory
# Note: default weights, strides, etc -> adjust in ConvRNN.py
BYPASSES = []  # bypasses: list of tuples (from, to)


# noinspection PyPep8
def get_layers(train):
    if not train:
        fc_keep_prob = None  # no dropout for eval mode
    else:
        fc_keep_prob = FC_KEEP_PROB
    layers = {1: ['ConvPool', {'state_size': LAYER_SIZES[1]['state'],
                               'output_size': LAYER_SIZES[1]['output'],
                               'conv_size': 11,  # kernel size for conv
                               'conv_stride': 4,  # stride for conv
                               'weight_decay': WEIGHT_DECAY,  # None for none
                               'pool_size': 3,
                               # kernel size for pool (defaults
                               # to = stride determined by layer sizes.),
                               'decay_param_init': DECAY_PARAM_INIT,
                               # (relevant if you have memory)
                               'memory': MEMORY}],
              2: ['ConvPool', {'state_size': LAYER_SIZES[2]['state'],
                               'output_size': LAYER_SIZES[2]['output'],
                               'conv_size': 5,  # kernel size for conv
                               'conv_stride': 1,  # stride for conv
                               'weight_decay': WEIGHT_DECAY,  # None for none
                               'pool_size': 3,  # kernel size for pool
                               'decay_param_init': DECAY_PARAM_INIT,
                               'memory': MEMORY}],
              3: ['Conv', {'state_size': LAYER_SIZES[3]['state'],
                               'conv_size': 3,  # kernel size for conv
                               'conv_stride': 1,  # stride for conv
                               'weight_decay': WEIGHT_DECAY,  # None for none
                               # kernel size for pool
                               'decay_param_init': DECAY_PARAM_INIT,
                               # (relevant if you have memory)
                               'memory': MEMORY}],
              4: ['Conv', {'state_size': LAYER_SIZES[4]['state'],
                           'conv_size': 3,  # kernel size for conv
                           'conv_stride': 1,  # stride for conv
                           'weight_decay': WEIGHT_DECAY,  # None for none
                           'decay_param_init': DECAY_PARAM_INIT,
                           'memory': MEMORY}],
              5: ['ConvPool', {'state_size': LAYER_SIZES[5]['state'],
                               'output_size': LAYER_SIZES[5]['output'],
                               'conv_size': 3,  # kernel size for conv
                               'conv_stride': 1,  # stride for conv
                               'weight_decay': WEIGHT_DECAY,  # None for none
                               'pool_size': 3,
                               'decay_param_init': DECAY_PARAM_INIT,
                               'memory': MEMORY}],
              6: ['FC', {'state_size': LAYER_SIZES[6]['state'],
                         'keep_prob': fc_keep_prob,
                         'memory': False}],
              7: ['FC', {'state_size': LAYER_SIZES[7]['state'],
                         'keep_prob': fc_keep_prob,
                         'memory': False}]
              }
    return layers


def toJSON(outfile, train=True):
    """
    :param train: True to return JSON with training parameters;
    otherwise JSON contains eval parameters
    :return: writes parameters to JSON file specified by outfile
    """
    LAYERS = get_layers(train=train)

    parameters = {  # image parameters
        'data_path': DATA_PATH,
        'image_size_orig': IMAGE_SIZE_ORIG,
        'image_size_crop': IMAGE_SIZE_CROP,
        'num_channels': NUM_CHANNELS,
        'pixel_depth': PIXEL_DEPTH,
        'num_labels': NUM_LABELS,
        'total_imgs_hdf5': TOTAL_IMGS_HDF5,

        # run configuration parameters
        'train_size': TRAIN_SIZE,
        'num_epochs': NUM_EPOCHS,
        'batch_size': BATCH_SIZE,
        'num_preprocess_threads': NUM_PREPROCESS_THREADS,
        'num_readers': NUM_READERS,
        'input_queue_memory_factor': INPUT_QUEUE_MEMORY_FACTOR,
        'log_device_placement': LOG_DEVICE_PLACEMENT,

        # saving paths
        'checkpoint_dir': CHECKPOINT_DIR,
        'save_path': SAVE_PATH,
        'save_loss': SAVE_LOSS,
        'save_loss_freq': SAVE_LOSS_FREQ,
        'save_vars': SAVE_VARS,
        'save_vars_freq': SAVE_VARS_FREQ,
        'max_to_keep': MAX_TO_KEEP,
        # tensorboard
        'tensorboard': TENSORBOARD,

        # restoring variables from file
        'restore_vars': RESTORE_VARS,
        'start_step': START_STEP,
        'restore_var_file': RESTORE_VAR_FILE,

        # graph parameters
        'T_tot': T_TOT,
        'layer_sizes': LAYER_SIZES,
        'weight_decay': WEIGHT_DECAY,
        'fc_keep_prob': FC_KEEP_PROB,
        'decay_param_init': DECAY_PARAM_INIT,
        'memory': MEMORY,
        'layers': LAYERS,
        'bypasses': BYPASSES,

        'initial_states': INITIAL_STATES,
        'input_seq': INPUT_SEQ
    }
    if train:
        parameters.update({
            # loss function parameter
            'time_penalty': TIME_PENALTY,

            # optimization parameters
            'grad_clip': GRAD_CLIP,
            'learning_rate_base': LEARNING_RATE_BASE,
            'learning_rate_decay_factor': LEARNING_RATE_DECAY_FACTOR,
            'momentum': MOMENTUM,
            'num_epochs_per_decay': NUM_EPOCHS_PER_DECAY

        })
    if not train:
        parameters.update({
            # add evaluation parameters
            'num_validation_batches': NUM_VALIDATION_BATCHES,
            'eval_batch_size': EVAL_BATCH_SIZE,

            # no dropout
            'fc_keep_prob': None
        })

    # write parameters dictionary to json
    with open(outfile, 'w') as f:
        json.dump(parameters, f)


if __name__ == "__main__":
    # take in json target file as argument
    parser = argparse.ArgumentParser('parameters to JSON')
    parser.add_argument('-o', '--out', default='params.json',
                        help='output JSON file', dest='out')
    parser.add_argument('--train', dest='train', action='store_true',
                        default=True,
                        help='Train model [default]')
    parser.add_argument('--eval', dest='train', action='store_false',
                        default=False,
                        help='Eval model')
    args = parser.parse_args()
    print('Training:', args.train)
    toJSON(outfile=args.out, train=args.train)
