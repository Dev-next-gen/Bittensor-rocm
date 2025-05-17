# 📚 Bittensor SDK - ROCm Edition 🫠🔦

[![Discord Chat](https://img.shields.io/discord/308323056592486420.svg)](https://discord.gg/bittensor) [![CodeQL](https://github.com/opentensor/bittensor/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/opentensor/bittensor/actions) [![PyPI version](https://badge.fury.io/py/bittensor.svg)](https://badge.fury.io/py/bittensor) [![Codecov](https://codecov.io/gh/opentensor/bittensor/graph/badge.svg)](https://app.codecov.io/gh/opentensor/bittensor) [![License: MIT](https://opensource.org/licenses/MIT)](https://opensource.org/licenses/MIT)

## 🛠️ Internet-scale Neural Networks

[Discord](https://discord.gg/bittensor) • [Network](https://taostats.io/) • [Research](https://bittensor.com/whitepaper) • [Documentation](https://docs.bittensor.com)

---

## ⚡ ROCm Version

This modified fork of Bittensor is 100% compatible with:

- ✅ PyTorch 2.4.0 ROCm
- ✅ ROCm 6.3.4 (multi-GPU AMD)
- ✅ Python 3.12
- ✅ Ubuntu 22.04 / Kernel 6.8+

🎯 **Goal:** Mine, validate, and explore Bittensor using an AMD ROCm rig – without CUDA or Docker dependencies.

---

## 🚨 BEFORE INSTALLING

You must install ROCm and PyTorch ROCm manually following this official guide:  
👉 [eliranwong/MultiAMDGPU_AIDev_Ubuntu](https://github.com/eliranwong/MultiAMDGPU_AIDev_Ubuntu)

---

## ✅ Quick Installation

```bash
git clone https://github.com/Dev-next-gen/Bittensor-rocm.git
cd Bittensor-rocm
chmod +x install.sh
./install.sh
source venv/bin/activate
```

---

## 🧪 Verify Installation

```bash
python3 -c "import bittensor; print(bittensor.__version__)"
btcli wallet list
```

**Expected output:**

```
TORCH HIP ACTIVE: True
BITTENSOR OK: 2.0.0
```

---

## ✅ Features Maintained

- Fully working `btcli`
- TAO wallet coldkey & hotkey support
- RPC / Axon / Metagraph communication
- ROCm-based mining support
- Subnet registration & synchronization

---

## 🧪 ROCm Test Suite

We provide an isolated ROCm test suite to validate functionality without invoking CUDA:

```bash
pytest
```

### Structure:

```text
rocm_tests/
├── __init__.py
├── test_imports_rocm.py
├── test_rocm_env.py
└── test_pow_smoke_rocm.py
```

### pytest.ini (at project root):

```text
[pytest]
minversion = 6.0
addopts = -ra -q
testpaths = rocm_tests
python_files = test_*.py
norecursedirs = tests/unit_tests
```

---

## 🔥 Additional Step: Compile bittensor_helpers Extension (for ROCm)

Bittensor ROCm requires compiling a custom extension (bittensor_helpers) to enable GPU PoW solving.

### Steps:

```bash
cd bittensor/_extensions
python setup.py clean --all
python setup.py build_ext --inplace
python setup.py install
```

If you encounter errors about `libc10.so` not found, please run:

```bash
export LD_LIBRARY_PATH=$(python -c 'import torch; import os; print(os.path.join(os.path.dirname(torch.__file__), "lib"))'):$LD_LIBRARY_PATH
```

*(Make it permanent by adding it to your `~/.bashrc`.)*

✅ After compilation, you will be able to use ROCm GPU acceleration in Bittensor.

---

## 🛠️ CLI Wallet Management (btcli)

After installation, you can manage wallets directly using the CLI:

```bash
# List available wallets
btcli wallet list

# Create a new coldkey
btcli wallet new-coldkey --wallet.name YourWalletName

# Create a new hotkey
btcli wallet new-hotkey --wallet.name YourWalletName --wallet.hotkey YourHotkeyName

# Regenerate a coldkey if needed
btcli wallet regen-coldkey --wallet.name YourWalletName
```

---

## 🛠️ CLI Metagraph Management (btcli)

You can also synchronize and inspect the Bittensor Metagraph:

```bash
# Synchronize the Metagraph
btcli metagraph sync

# Overview the Metagraph
btcli metagraph overview
```

---

## 🧪 Wallet Management via Python

Example if you want to interact manually in Python:

```python
from bittensor_wallet import Wallet

# Load existing wallet
wallet = Wallet(name="YourWalletName", hotkey="YourHotkeyName")

print(f"Coldkey Address: {wallet.coldkeypub.ss58_address}")
print(f"Hotkey Address: {wallet.hotkey.ss58_address}")
```

✅ Full coldkey/hotkey control directly in Python.

---

## 💖 Support / Donation

Want to support this ROCm fork?  
Donate to:

```
0xa46381Ad9febd785449074A0e3D8146c7d9Fd9ab
```

*(ETH / TAO compatible)*

---

## 📜 License

The MIT License (MIT)  
Copyright © 2025 Leo CAMUS

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## 🙏 Acknowledgements

This project integrates/inspires from:

## 📎 Related Projects

- [Bittensor (Official OpenTensor Repo)](https://github.com/opentensor/bittensor)
- [ROCm multi-GPU integration by eliranwong](https://github.com/eliranwong/MultiAMDGPU_AIDev_Ubuntu)
- Community support from Linux/AMD open-source contributors

  Soon i will drop full process for build AMD inference serve with 8GPU RX7900XT
