# ParaSuit - Benchmarks

To run ParaSuit, you have to modify the following three files in KLEE-2.1.

| File | location |
|:------:|:------------|
| ExecutionState.h   | klee/include/klee/ExecutionState.h |
| ExecutionState.cpp | klee/lib/Core/ExecutionState.cpp   |
| Executor.cpp       | klee/lib/Core/Executor.cpp         |

When building our tool in Docker, this step can be skipped since the corresponding files are automatically replaced.
