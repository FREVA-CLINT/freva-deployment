#!/bin/bash
### A simple bash script that installs and creates freva and some additional software
# Function to display help message
show_help() {
    echo "Usage: $0 -p prefix"
    echo "  -p, --prefix    Specify the installation prefix for the conda environment"
}

# Check if conda or mamba is installed
mamba_bin=$(command -v mamba)
conda_bin=$(command -v conda)

# Use mamba if available, otherwise use conda
pkg_bin=${mamba_bin:-$conda_bin}

# Initialize variables
prefix=""

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -p|--prefix)
            if [ -n "$2" ] && [[ ${2:0:1} != "-" ]]; then
                prefix="$2"
                shift 2
            else
                echo "Error: --prefix requires a non-empty option argument."
                exit 1
            fi
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if prefix is set
if [ -z "$prefix" ]; then
    echo "Error: --prefix is required."
    show_help
    exit 1
fi

set -Eeuo pipefail
# Function to download a file using nc and built-in bash tools
# Function to install micromamba if necessary
install_micromamba() {
    local arch
    case $(uname -m) in
        x86_64) arch=linux-64 ;;
        aarch64) arch=linux-aarch64 ;;
        ppc64le) arch=linux-ppc64le ;;
        *)
            echo "Unsupported architecture: $(uname -m)"
            exit 1
            ;;
    esac
    curr_dir=$(pwd)
    local temp_dir=$(mktemp -d)
    cd "$temp_dir" || { echo "Failed to create temporary directory"; exit 1; }
    curl -Ls https://micro.mamba.pm/api/micromamba/$arch/latest | tar -xvj bin/micromamba
    ./bin/micromamba create -c conda-forge -p "$prefix" -y python=3.12 freva
    cd $curr_dir
    rm -rf "$temp_dir"
}

rm -rf $prefix

# Create conda environment
if [ -z "$pkg_bin" ]; then
    install_micromamba
else
    $pkg_bin create -c conda-forge -p "$prefix" -y python=3.12 freva
fi

# Check if environment creation was successful
if [ $? -ne 0 ]; then
    echo "Failed to create conda environment at $prefix"
    exit 1
fi

echo "Installing additional packages via pip"
"$prefix/bin/python" -m pip install jupyter-kernel-install metadata-inspector

echo "Installing metadata-crawler"
curl -s https://swift.dkrz.de/v1/dkrz_6681fd49-d4e5-44f6-bf39-307a187ed22e/data-crawler/data-crawler-linux64 -o  $prefix/sbin/data-crawler
chmod +x "$prefix/sbin/data-crawler"
echo "Installation completed successfully"
