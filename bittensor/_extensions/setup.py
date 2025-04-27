from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CppExtension

setup(
    name='bittensor_helpers',
    ext_modules=[
        CppExtension(
            name='bittensor_helpers',
            sources=['bittensor_helpers/ops.cpp'],
            extra_compile_args={'cxx': ['-O3', '-fopenmp']},
        ),
    ],
    cmdclass={'build_ext': BuildExtension}
)
