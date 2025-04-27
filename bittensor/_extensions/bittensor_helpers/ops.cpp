#include <torch/extension.h>

torch::Tensor solve_blocks(torch::Tensor input) {
    return input + 1;
}

TORCH_LIBRARY(bittensor_helpers, m) {
    m.def("solve_blocks", &solve_blocks);
}
