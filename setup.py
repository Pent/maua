#!/usr/bin/env python
from setuptools import find_packages, setup

setup(
    name="maua",
    version="0.4",
    description="Deep learning toolkit for image, video, and audio synthesis",
    author="Hans Brouwer",
    author_email="hans@wavefunk.xyz",
    url="https://github.com/maua-maua-maua/maua",
    packages=find_packages(include="maua*"),
    install_requires=[
        "apex @ git+https://github.com/NVIDIA/apex",
        "auraloss",
        "av",
        "basicsr @ git+https://github.com/JCBrouwer/BasicSR@feature/dynamic-import-torch",  # TODO hopefully basicsr fixes install-time torch dep
        "bitsandbytes-cuda113",
        "cached_conv @ git+https://github.com/caillonantoine/cached_conv",
        "click",
        "clip",
        "cupy-cuda116",
        "cython",
        "decord",
        "dill",
        "easydict",
        "effortless_config",
        "einops",
        "ffmpeg_python",
        "ftfy",
        "gdown",
        "glumpy",
        "gputil",
        "h5py",
        "imageio_ffmpeg",
        "joblib",
        "kornia",
        "librosa",
        "lpips",
        "madmom @ git+https://github.com/CPJKU/madmom",  # TODO madmom==0.17 includes fix for install-time Cython dep
        "matplotlib",
        "medpy",
        "mmflow",
        "mmcv",
        "more_itertools",
        "ninja",
        "npy_append_array",
        "numba",
        "numpy",
        "nvidia-cuda-runtime-cu116",
        "nvidia-cuda-nvcc-cu116",
        "nvidia-cudnn",
        "nvidia-tensorrt",
        "omegaconf",
        "openunmix",
        "pandas",
        "prdc",
        "py7zr",
        "pyglet",
        "pyopengl",
        "pyspng",
        "pytorch_lightning",
        "PyYaml",
        "ranger @ git+https://github.com/lessw2020/Ranger-Deep-Learning-Optimizer",
        "ranger21 @ git+https://github.com/lessw2020/Ranger21",
        "realesrgan",
        "requests",
        "resampy",
        "resize_right",
        "scikit_learn",
        "scipy",
        "seaborn",
        "sentencepiece",
        "sklearn",
        "soundfile",
        "tensorboard",
        "tensorboardX",
        "termcolor",
        "timm",
        "torch",
        "torch_optimizer",
        "torchaudio",
        "torchcrepe",
        "torchvision",
        "tqdm",
        "transformers",
        "udls @ git+https://github.com/caillonantoine/UDLS",
        "unidecode",
        "wandb",
        "youtokentome",
    ],
)
