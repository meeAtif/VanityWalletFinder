# Vanity Wallet Finder Pro

[![Download for Windows](https://img.shields.io/badge/Download-Windows_EXE-blue?style=for-the-badge&logo=windows)](https://github.com/meeAtif/VanityWalletFinder/releases/latest/download/VanityWalletFinder.exe)

A high-performance, multi-process crypto vanity wallet generator with a modern GUI. 
Supports **Bitcoin (Legacy & SegWit)** and **Ethereum**.


## Features

-   **Multi-Currency**: Generate ETH, BTC (Legacy), and BTC (SegWit) addresses.
-   **Custom Patterns**: 
    -   Starts with (e.g., `0xDEAD`, `1Ask`)
    -   Ends with
    -   Contains
    -   Repeating characters
-   **Advanced Configuration**:
    -   **Word Count**: Choose between 12-word (Legacy) or 24-word (High Security) mnemonics.
    -   **Search Scope**: Scan the "First 1", "First 5", or a "Specific" index address per mnemonic.
    -   **Export Control**: Toggle "Export .txt" to save or discard found wallets.
-   **High Performance**: Uses `bip_utils` and multiprocessing to utilize all CPU cores.
-   **Modern GUI**: Built with CustomTkinter for a clean, dark-mode interface.
-   **Standalone**: Available as a single `.exe` file for Windows (no Python required).

## Installation

### Option 1: Run Executable (Easiest)
1.  Go to the [Releases](../../releases) page.
2.  Download `VanityWalletFinder.exe`.
3.  Run the application.

### Option 2: Run from Source
1.  Install Python 3.8+.
2.  Clone the repository:
    ```bash
    git clone https://github.com/meeAtif/VanityWalletFinder.git
    cd VanityWalletFinder
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the app:
    ```bash
    python gui.py
    ```

## Building the Executable

If you want to build the `.exe` yourself:
```bash
python build_exe.py
```
The executable will be in the `dist` folder.

## Disclaimer

**Security Notice**: This tool generates private keys and mnemonics locally on your machine.
-   The code is open source; verify it yourself.
-   Never share your mnemonics or private keys.
-   Run this on a secure, offline machine if possible.

## License

MIT
