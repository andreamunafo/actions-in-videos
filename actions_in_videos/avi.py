# AUTOGENERATED! DO NOT EDIT! File to edit: dev/02_avi.ipynb (unless otherwise specified).

__all__ = ['AVI']

# Cell
import numpy as np
import cv2
import pathlib
import matplotlib.pyplot as plt
from PIL import Image

import torch

# Cell
class AVI:
    def __init__(self, filename, toPIL=False, verbose=False):
        self._filename = pathlib.Path(filename)
        self._toPIL = toPIL
        self._verbose = verbose
        cap = cv2.VideoCapture(self._filename.as_posix())
        self._attributes = {}
        self._attributes['n-frames']     = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._attributes['frame-height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._attributes['frame-width']  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._attributes['channels']    = None # default
        self._attributes['fps']         = cap.get(cv2.CAP_PROP_FPS)

        # call this function here to update some attributes that are only available once a frame is grabbed.
        self.getFrame(0)

        cap.release()

    def __len__(self):
        return self._attributes['n-frames']

    def getFrame(self, frame_index, circular=False):
        """Loads a single frame from a file at index frame_index.

        The data is returned and is a numpy array of size [n_channels, height, width] of type np.float32.
        If circular == True, wraps frame_index to the number of frames
        """
        ### load file from AVI
        cap = cv2.VideoCapture(self._filename.as_posix())

        if not cap.isOpened():
            print(f"could not open {self._filename.as_posix()}")
            frame = np.array([])
            return frame

        if circular: frame_index = frame_index % self._attributes['n-frames']
        self._attributes['frame-index']  = frame_index;

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        frameId = cap.get(cv2.CAP_PROP_POS_FRAMES) # current frame number
        ret, frame = cap.read()
        if frame is None:
            if self._verbose: print(f'ERROR in file: {self._filename.as_posix()}, frame-index: {frame_index}.')
            return frame
        cap.release()

        if len(frame.shape) == 2:
            self._attributes['channels'] = 2
        else:
            self._attributes['channels'] = frame.shape[2]

        if self._toPIL: # .transpose(2,0,1)
            cv2_im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = Image.fromarray(cv2_im)
        else:
            #frame = frame.astype(np.float32)
            frame = frame.astype(np.uint8)

        return frame

    def getRandomFrame(self, max_attempts=100):
        frame = None
        count = 0
        frame_index = None
        while frame is None and count < max_attempts:
            count += 1
            if frame_index is None:
                frame_index = np.random.randint(self._attributes['n-frames'])
                frame = self.getFrame(frame_index)
                if frame is None:
                    if self._verbose: print(f'ERROR in file: {self._filename}, frame_index: {frame_index}. Retrying with different random frame number.')
                    frame_index = None
        return frame

    def getFrames(self, c, w, h, reshape=False, to_net_shape=False, normalise=False):
        # c, w, h = channels, width, heigth
        data = np.zeros((self._attributes['n-frames'], c, w, h), dtype=np.float32)

        for j in range(self._attributes['n-frames']):
            frame = avi.getFrame(j)
            if reshape: frame = self.reshape(frame, (w, h))
            if normalise:  frame = self.normalise(frame)
            if to_net_shape: frame = AVI.toNetShape(frame)
            data[j,:,:,:] = frame
#             AVI.frameShow(AVI.toImgShape(frame), avi._filename)
        return data

    def getSequence(self, idx_0, seq_len, sample_interval=1, circular=False):
        """
        returns:
        - data: numpy matrix of shape seq_len x H x W x C
        """
        assert sample_interval >= 1, "sample_interval must be >= 1"
        assert idx_0 <= self._attributes['n-frames'] - seq_len, f"selected sequence indices are out of range: video length is {len(self)}"

        if seq_len > self._attributes['n-frames']:
            seq_len = self._attributes['n-frames']

        # c, w, h = channels, width, heigth
        data = np.zeros((seq_len,
                         self._attributes['frame-height'],
                         self._attributes['frame-width'],
                         self._attributes['channels']), dtype=np.uint8)

        if self._verbose:
            print(f"video attributes: {self._attributes}")

        for j in range(0, seq_len):
            frame_index = idx_0+j*sample_interval
            if self._verbose: print(f'grabbing frame number: {frame_index}')

            data[j,:,:,:] = self.getFrame(frame_index, circular)
        return data

    def getRandomSequence(self, seq_len, sample_interval):
        """
        returns:
        - data: numpy matrix of shape seq_len x H x W x C
        """
        idx_0 = np.random.randint(0, self._attributes['n-frames']-seq_len)
        if self._verbose:
            print(f"sequence idx_0: {idx_0}, sequence_length: {seq_len}, num of frames: {self._attributes['n-frames']}")
        data = self.getSequence(idx_0, seq_len, sample_interval)
        return data

    @staticmethod
    def toNetShape(frame):
        # this function simply checks if the frame
        # is in the format Channels x Width x Height.
        if frame.shape[0] > 3:
#            frame.transpose(0, 1, 2)
            frame = frame.transpose(2, 0, 1)
        return frame

    @staticmethod
    def toImgShape(frame):
        if frame.shape[2] > 3:
            frame = frame.transpose(1, 2, 0)
        return frame

    @staticmethod
    def toImg(frame, normalise=True):
        # Checks if a tensor
        if type(frame) == torch.Tensor:
            frame = frame.data.numpy()
            # tensor images are usually in the form of channels x width x height
            #frame = frame.transpose(1, 2, 0)
            AVI.toImgShape(frame)

        # Normalises it to be ready to plot it with imshow.
        if normalise:
            frame = (frame-np.min(frame))/np.max(frame-np.min(frame))
        return frame

#     def frameShow(self, frame, title=None):
#         plt.imshow(AVI.toImg(frame))
#         if title is None:
#             title = self._filename
#         plt.title(title)

    @staticmethod
    def frameShow(frame, title=None):
        plt.imshow(AVI.toImg(frame))
        if title is not None:
            plt.title(title)

    @staticmethod
    def sequenceShow(sequence, title=None):
        if isinstance(sequence, list):
              seq_len=len(sequence)
        else:
            seq_len = sequence.shape[0] # numpy matrix
        ncols = int(np.ceil(np.sqrt(seq_len)))
        for i in range(seq_len):
            ax = plt.subplot(ncols, ncols, i+1)
            AVI.frameShow(sequence[i])

    def set_normalisation(self, mean, std):
        self._attributes['mean'] = mean
        self._attributes['std'] = std

    def normalise(self, frame):
        frame = frame/255.0
        frame = (frame - self._attributes['mean'])/self._attributes['std']
        return frame

    def reshape(self, frame, out_shape):
        # out_shape is a tuple: (IMAGE_SIZE,IMAGE_SIZE)
        frame = cv2.resize(frame, out_shape)
        return frame

