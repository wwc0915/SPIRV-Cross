#!/bin/bash
# Test script for HW extension shaders.
# Uses the custom glslang + spirv-tools build at /home/riflebird/glslang-dev/build.
#
# Usage:
#   ./test_hw_shaders.sh              # run regression tests (continue on failure, print stats)
#   ./test_hw_shaders.sh --update     # update reference files
#   ./test_hw_shaders.sh --diff       # show diff on failure
#   ./test_hw_shaders.sh --parallel   # run tests in parallel

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GLSLANG_BUILD="/home/riflebird/glslang-dev/build"

GLSLANG="${GLSLANG_BUILD}/StandAlone/glslangValidator"
SPIRV_AS="${GLSLANG_BUILD}/External/spirv-tools/tools/spirv-as"
SPIRV_VAL="${GLSLANG_BUILD}/External/spirv-tools/tools/spirv-val"
SPIRV_OPT="${GLSLANG_BUILD}/External/spirv-tools/tools/spirv-opt"
SPIRV_CROSS="${SCRIPT_DIR}/spirv-cross"

if [ ! -x "${SPIRV_CROSS}" ]; then
	echo "Building spirv-cross"
	make -C "${SCRIPT_DIR}" -j$(nproc) || exit 1
	SPIRV_CROSS="${SCRIPT_DIR}/spirv-cross"
fi

echo "Using glslangValidator: ${GLSLANG}"
echo "Using spirv-val:        ${SPIRV_VAL}"
echo "Using spirv-cross:      ${SPIRV_CROSS}"

# The reference_path() in test_shaders.py derives the reference directory from
# os.path.split(folder).  To place references at reference/hw/ (project root,
# matching the existing convention), folder must be a bare top-level name "hw".
# Create a temporary symlink so os.walk can traverse shaders/hw/ via "hw".
ln -s shaders/hw "${SCRIPT_DIR}/hw"
trap 'rm -f "${SCRIPT_DIR}/hw"' EXIT

python3 "${SCRIPT_DIR}/test_shaders.py" hw \
	--spirv-cross "${SPIRV_CROSS}" \
	--glslang "${GLSLANG}" \
	--spirv-as "${SPIRV_AS}" \
	--spirv-val "${SPIRV_VAL}" \
	--spirv-opt "${SPIRV_OPT}" \
	--continue \
	"$@"
TEST_RESULT=$?

echo "HW shader tests completed!"
exit ${TEST_RESULT}
