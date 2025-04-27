# 📚 **Installation and Compilation Guide for the ROCm Extension (`bittensor_helpers`)**

This guide provides detailed instructions to configure and compile the custom ROCm extension (`bittensor_helpers`) for the **Bittensor ROCm** project.

---

## 🛠️ **Requirements**

- **ROCm 6.3.4** installed
- **PyTorch 2.4.0 ROCm** installed
- **Python 3.12** with `pip`
- Ubuntu (recommended: 22.04 or higher)

If you don't have these installed, [follow this ROCm setup guide](https://github.com/eliranwong/MultiAMDGPU_AIDev_Ubuntu) first.

---

## 📌 **Install Dependencies**

Run the following commands to install all necessary build tools:

```bash
pip install setuptools wheel ninja
```

Ensure these packages are properly installed to avoid build errors.

---

## 🧹 **Compile the ROCm Extension (`bittensor_helpers`)**

Navigate to your **Bittensor-rocm** project root.

### 1⃣⃣ **Create the `ops.cpp` file**

```bash
cat <<EOF > bittensor/_extensions/bittensor_helpers/ops.cpp
#include <torch/extension.h>

// Simple test function
torch::Tensor solve_blocks(torch::Tensor input) {
    return input + 1;
}

// Explicit binding for torch.ops
TORCH_LIBRARY(bittensor_helpers, m) {
    m.def("solve_blocks", &solve_blocks);
}
EOF
```

### 2⃣⃣ **Edit `setup.py`**

Create or edit the file `bittensor/_extensions/setup.py` to include only `ops.cpp`:

```python
from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CppExtension

setup(
    name='bittensor_helpers',
    ext_modules=[
        CppExtension(
            'bittensor_helpers',
            ['bittensor_helpers/ops.cpp'],
        ),
    ],
    cmdclass={'build_ext': BuildExtension}
)
```

### 3⃣⃣ **Build the extension**

```bash
cd bittensor/_extensions
python setup.py clean --all
python setup.py build_ext --inplace
python setup.py install
```

---

## 🧪 **Test the compiled extension**

Verify that the extension is properly compiled and loaded:

```bash
python -c "import torch; torch.ops.load_library('bittensor_helpers.cpython-312-x86_64-linux-gnu.so'); print(torch.ops.bittensor_helpers.solve_blocks(torch.tensor([1.0, 2.0])))"
```

Expected output:

```bash
tensor([2., 3.])
```

---

## 🔧 **Troubleshooting Common Errors**

**Error:** `libc10.so` not found

**Solution:**

```bash
export LD_LIBRARY_PATH=$(python -c 'import torch; import os; print(os.path.join(os.path.dirname(torch.__file__), "lib"))'):$LD_LIBRARY_PATH
```

Make it permanent by adding to your `.bashrc`:

```bash
echo 'export LD_LIBRARY_PATH=$(python -c "import torch; import os; print(os.path.join(os.path.dirname(torch.__file__), \"lib\"))"):$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

---

## ✅ **Finalize and Clean Up**

After compilation, clean up build artifacts if needed:

```bash
python setup.py clean --all
```

---

## 📖 **Additional References**

- [Official ROCm Documentation](https://github.com/RadeonOpenCompute/ROCm)
- [PyTorch ROCm Setup](https://pytorch.org/get-started/locally/#rocm-version)
- [Official Bittensor GitHub](https://github.com/opentensor/bittensor)

---

✅ **You are now ready to use the ROCm extension with Bittensor!**
