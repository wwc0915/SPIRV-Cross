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

# ---------------------------------------------------------------------------
# 1. GLSL backend regression tests (OpenGL + Vulkan GLSL via .vk. marker)
# ---------------------------------------------------------------------------
echo "=== GLSL backend regression tests ==="
python3 "${SCRIPT_DIR}/test_shaders.py" hw \
	--spirv-cross "${SPIRV_CROSS}" \
	--glslang "${GLSLANG}" \
	--spirv-as "${SPIRV_AS}" \
	--spirv-val "${SPIRV_VAL}" \
	--spirv-opt "${SPIRV_OPT}" \
	--target-env vulkan1.3 \
	--continue \
	"$@"
GLSL_RESULT=$?

# ---------------------------------------------------------------------------
# 2. Non-GLSL backend rejection tests (MSL / HLSL)
#    HW extensions are GLSL-only; spirv-cross --msl / --hlsl must reject them.
# ---------------------------------------------------------------------------
echo ""
echo "=== Non-GLSL backend rejection tests (MSL / HLSL) ==="

reject_pass=0
reject_fail=0

# Find all GLSL HW shader source files (.comp / .vert / .frag, skip .spv binaries)
hw_sources=$(find "${SCRIPT_DIR}/shaders/hw" -type f \( -name '*.comp' -o -name '*.vert' -o -name '*.frag' \) | sort)

for src in ${hw_sources}; do
	# Compile to SPIR-V
	spvmk=$(mktemp --suffix=.spv)
	if ! "${GLSLANG}" --amb --target-env vulkan1.1 -V -o "${spvmk}" "${src}" 2>/dev/null; then
		# Shader may use SPIR-V 1.6 features; retry with spirv1.6
		if ! "${GLSLANG}" --amb --target-env spirv1.6 -V -o "${spvmk}" "${src}" 2>/dev/null; then
			rm -f "${spvmk}"
			continue
		fi
	fi

	relname=$(echo "${src}" | sed "s|${SCRIPT_DIR}/shaders/hw/||")

	for backend in --msl --hlsl; do
		# spirv-cross is expected to FAIL (non-zero exit)
		if "${SPIRV_CROSS}" --entry main "${backend}" -o /dev/null "${spvmk}" 2>/dev/null; then
			echo "FAIL  ${relname}  ${backend}: expected rejection but spirv-cross succeeded"
			reject_fail=$((reject_fail + 1))
		else
			echo "PASS  ${relname}  ${backend}: correctly rejected"
			reject_pass=$((reject_pass + 1))
		fi
	done

	rm -f "${spvmk}"
done

echo ""
echo "Rejection tests: passed=${reject_pass}  failed=${reject_fail}"

TOTAL_FAIL=$((GLSL_RESULT != 0 ? 1 : 0))
TOTAL_FAIL=$((TOTAL_FAIL + reject_fail))

echo ""
echo "========================================"
echo "HW shader tests completed!"
echo "========================================"
exit ${TOTAL_FAIL}
