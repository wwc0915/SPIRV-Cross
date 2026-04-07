; SPIR-V assembly for OpCooperativeMatrixLoadHW testing
; Requires SPIR-V 1.6

               OpCapability Shader
               OpCapability CooperativeMatrixHW
          %1 = OpExtInstImport "GLSL.std.450"
               OpMemoryModel Logical GLSL450
               OpEntryPoint GLCompute %main "main"
               OpExecutionMode %main LocalSize 16 1 1 1
               OpSource GLSL 450
               OpName %main "main"
               OpName %data "data"
               OpName %matA "matA"
               OpName %matB "matB"
               OpDecorate %data Binding 0
               OpDecorate %data DescriptorSet 0

        %uint = OpTypeInt 32 0
        %v2uint = OpTypeVector %uint 2
      %float = OpTypeFloat 32
%float_ptr_StorageBuffer = OpTypePointer StorageBuffer %float
        %100 = OpConstant %uint 16
        %101 = OpConstant %uint 16
        %102 = OpConstant %uint 0
        %103 = OpConstant %uint 1
        %200 = OpConstantComposite %v2uint %100 %101
        %201 = OpConstantComposite %v2uint %102 %102

; OpTypeCooperativeMatrixHW: <id> <component_type> <rows> <cols> <use>
; use: 0=MatrixA, 1=MatrixB, 2=Accumulator
        %coopmat_type_A = OpTypeCooperativeMatrixHW %float %100 %101 %102
        %coopmat_type_B = OpTypeCooperativeMatrixHW %float %100 %101 %103

        %data = OpVariable %float_ptr_StorageBuffer StorageBuffer

       %main = OpFunction %void None
        %10 = OpLabel
        %matA = OpCooperativeMatrixLoadHW %coopmat_type_A %data %200 %201 %102
        %matB = OpCooperativeMatrixLoadHW %coopmat_type_B %data %200 %201 %103
               OpReturn
               OpFunctionEnd
