# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SPIRV-Cross is a tool and library for parsing SPIR-V shader bytecode and converting it to other shader languages: GLSL, Metal Shading Language (MSL), HLSL, C++ (deprecated), and JSON reflection format.

## Build Commands

### CMake (Recommended)

```bash
# Create build directory and build
mkdir -p build && cd build
cmake ..
cmake --build . -j$(nproc)

# Build with tests enabled (requires glslang and SPIRV-Tools)
cmake -DSPIRV_CROSS_ENABLE_TESTS=ON ..

# Run tests via ctest
ctest -j$(nproc)

# Build options
cmake -DSPIRV_CROSS_STATIC=ON/OFF \      # Static libraries (default ON)
      -DSPIRV_CROSS_SHARED=ON/OFF \      # Shared library (default OFF)
      -DSPIRV_CROSS_CLI=ON/OFF \         # CLI binary (default ON)
      -DSPIRV_CROSS_ENABLE_TESTS=ON/OFF  # Tests (default ON)
```

### Makefile (Fallback - CLI only)

```bash
make -j$(nproc)           # Build CLI tool
make clean                # Clean build artifacts
DEBUG=1 make              # Debug build
```

## Testing

```bash
# Setup test dependencies (first time only)
./checkout_glslang_spirv_tools.sh   # Clone glslang and SPIRV-Tools
./build_glslang_spirv_tools.sh      # Build them

# Run full test suite
./test_shaders.sh

# Run specific test categories
python3 test_shaders.py shaders                           # GLSL output
python3 test_shaders.py --msl shaders-msl                 # MSL output
python3 test_shaders.py --hlsl shaders-hlsl               # HLSL output
python3 test_shaders.py --reflect shaders-reflection      # JSON reflection

# Update reference outputs after legitimate changes
./update_test_shaders.sh
```

## Code Formatting

```bash
./format_all.sh   # Format all source files with clang-format
```

## Architecture

### Compiler Class Hierarchy

```
Compiler (spirv_cross.cpp/hpp)
  └── CompilerGLSL (spirv_glsl.cpp/hpp)
        ├── CompilerMSL (spirv_msl.cpp/hpp)
        ├── CompilerHLSL (spirv_hlsl.cpp/hpp)
        ├── CompilerCPP (spirv_cpp.cpp/hpp) [deprecated]
        └── CompilerReflect (spirv_reflect.cpp/hpp)
```

### Core Modules

| File | Purpose |
|------|---------|
| `spirv_cross.cpp/hpp` | Base `Compiler` class - SPIR-V parsing, reflection, IR manipulation |
| `spirv_parser.cpp/hpp` | SPIR-V binary parser |
| `spirv_cross_parsed_ir.cpp/hpp` | Parsed intermediate representation |
| `spirv_cfg.cpp/hpp` | Control flow graph analysis |
| `spirv_glsl.cpp/hpp` | GLSL backend (base for MSL/HLSL) |
| `spirv_msl.cpp/hpp` | Metal Shading Language backend |
| `spirv_hlsl.cpp/hpp` | HLSL backend |
| `spirv_cross_c.cpp/h` | C API wrapper (ABI-stable) |
| `spirv_cross_util.cpp/hpp` | Utility functions |

### Key Types

- `Compiler`: Main entry point - parse SPIR-V and compile to target language
- `ShaderResources`: Reflection data for uniforms, storage buffers, stage inputs/outputs, etc.
- `Resource`: Individual shader resource with ID, type, and name

## Test Shader Directories

- `shaders/` - GLSL regression tests
- `shaders-msl/` - Metal output tests
- `shaders-hlsl/` - HLSL output tests
- `shaders-reflection/` - JSON reflection tests
- `shaders-no-opt/`, `shaders-msl-no-opt/`, `shaders-hlsl-no-opt/` - Tests without optimization
- `reference/` - Expected output for regression testing

## Notes

- C++11 standard required
- C++ API is not ABI-stable; use C API (`spirv_cross_c.h`) for shared library usage
- Changes to output must update reference files via `update_test_shaders.sh`
