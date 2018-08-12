import pycuda.driver as cuda
import pycuda.autoinit
from pycuda.driver import Context
from pycuda.compiler import SourceModule, DEFAULT_NVCC_FLAGS
from pycuda import gpuarray
import numpy as np


class CudaFunc:
    def __init__(self, mod, func_name):
        self.name = func_name
        self.mod = mod
        self.mods = {}
    def __call__(self, *args, precision='double', **kwargs):
        if not precision in self.mods:
            self.mods[precision] = self.mod.compile(precision)
        mod = self.mods[precision]
        f = mod.get_function(self.name)
        # automatically convert a few python types to their c equivalent here
        args = list(args)
        for (i,a) in enumerate(args):
            if isinstance(a, int):
                args[i] = np.int32(a)
        ret = f(*args, **kwargs)
        return ret

class CudaModule:
    def __init__(self, cuda_source, extra_nvcc_flags=[]):
        self.source = cuda_source
        self.nvcc_flags = DEFAULT_NVCC_FLAGS + ['-std=c++11'] + extra_nvcc_flags
    def compile(self, precision='single'):
        if precision == 'single':
            nvcc_flags = self.nvcc_flags + ['-DReal=float', '-DComplex=cuFloatComplex']
        elif precision == 'double':
            nvcc_flags = self.nvcc_flags + ['-DReal=double', '-DComplex=cuDoubleComplex']
        else:
            raise Exception('Unrecognized precision: {}'.format(precision))

        return SourceModule(self.source, options=nvcc_flags, no_extern_c=True)
    def func(self, func_name):
        return CudaFunc(self, func_name)
