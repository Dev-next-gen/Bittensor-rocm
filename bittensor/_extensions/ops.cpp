#include <torch/extension.h>

// Déclaration minimale nécessaire pour PyTorch ROCm
torch::Tensor solve_blocks(torch::Tensor input);

// Binding Python uniquement, implémentation dans ops_hip.cpp
PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("solve_blocks", &solve_blocks, "Solve blocks minimal ROCm");
}
