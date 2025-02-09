# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import pytest

pytest.importorskip("ethosu.vela")
import tvm
from tvm.script import tir as T
from tvm import relay
from tvm.relay.testing import run_opt_pass
from tvm.relay.backend.contrib.ethosu.tir.compiler import _lower_to_tir
from tvm.relay.backend.contrib.ethosu.tir.scheduler import copy_constants, OperatorCompute

from .infra import make_ethosu_conv2d


# fmt: off
@tvm.script.ir_module
class ReferenceModule:
    @T.prim_func
    def main(placeholder_3: T.Buffer[(8192,), "int8"], ethosu_write_1: T.Buffer[(2048,), "int8"]) -> None:
        # function attr dict
        T.func_attr({"from_legacy_te_schedule": True, "global_symbol": "main", "tir.noalias": True})
        buffer = T.buffer_decl([80], "uint8")
        buffer_1 = T.buffer_decl([304], "uint8")
        T.preflattened_buffer(placeholder_3, [1, 16, 16, 32], dtype="int8", data=placeholder_3.data)
        T.preflattened_buffer(ethosu_write_1, [1, 16, 16, 8], dtype="int8", data=ethosu_write_1.data)
        # body
        placeholder_global = T.allocate([304], "uint8", "global", annotations={"disable_lower_builtin": True})
        placeholder_d_global = T.allocate([80], "uint8", "global", annotations={"disable_lower_builtin": True})
        T.evaluate(T.call_extern("ethosu_copy", buffer_1[0], 304, placeholder_global[0], dtype="handle"))
        T.evaluate(T.call_extern("ethosu_copy", buffer[0], 80, placeholder_d_global[0], dtype="handle"))
        T.evaluate(T.call_extern("ethosu_conv2d", "int8", 16, 16, 32, 16, 0, 16, placeholder_3[0], 0, 0, 0, T.float32(0.5), 10, "NHWC", 512, 32, 1, "int8", 16, 16, 8, 16, 0, 16, ethosu_write_1[0], 0, 0, 0, T.float32(0.25), 14, "NHWC", 128, 8, 1, 1, 1, 1, 1, 1, 1, placeholder_global[0], 304, T.int8(-1), T.int8(-1), 12, placeholder_d_global[0], 80, T.int8(-1), T.int8(-1), 0, 0, 0, 0, "NONE", 0, 0, "TFL", "NONE", 0, 0, 0, dtype="handle"))
    __tvm_meta__ = None
# fmt: on


def test_copy():
    def _get_func():
        data = relay.var("data", shape=(1, 16, 16, 32), dtype="int8")
        conv = make_ethosu_conv2d(
            data,
            32,
            8,
            (1, 1),
            (0, 0),
            (1, 1),
            (1, 1),
        )
        func = relay.Function(relay.analysis.free_vars(conv), conv)
        func = run_opt_pass(func, relay.transform.InferType())
        return func

    func = _get_func()
    mod, _ = _lower_to_tir(func, cascader=copy_constants())

    script = mod.script(show_meta=True)
    test_mod = tvm.script.from_source(script)
    reference_mod = ReferenceModule
    tvm.ir.assert_structural_equal(test_mod["main"], reference_mod["main"], True)


# fmt: off
@tvm.script.ir_module
class WeightStream:
    @T.prim_func
    def main(placeholder_5: T.Buffer[(8192,), "int8"], ethosu_write_1: T.Buffer[(4096,), "int8"]) -> None:
        # function attr dict
        T.func_attr({"from_legacy_te_schedule": True, "global_symbol": "main", "tir.noalias": True})
        buffer = T.buffer_decl([416], "uint8")
        buffer_1 = T.buffer_decl([112], "uint8")
        buffer_2 = T.buffer_decl([272], "uint8")
        buffer_3 = T.buffer_decl([64], "uint8")
        T.preflattened_buffer(placeholder_5, [1, 16, 16, 32], dtype="int8", data=placeholder_5.data)
        T.preflattened_buffer(ethosu_write_1, [1, 16, 16, 16], dtype="int8", data=ethosu_write_1.data)
        # body
        placeholder_global_unrolled_iter_0 = T.allocate([416], "uint8", "global", annotations={"disable_lower_builtin": True})
        placeholder_global_unrolled_iter_1 = T.buffer_decl([272], "uint8", data=placeholder_global_unrolled_iter_0.data)
        placeholder_d_global_unrolled_iter_0 = T.allocate([112], "uint8", "global", annotations={"disable_lower_builtin": True})
        placeholder_d_global_unrolled_iter_1 = T.buffer_decl([64], dtype="uint8", data=placeholder_d_global_unrolled_iter_0.data)
        T.evaluate(T.call_extern("ethosu_copy", buffer[0], 416, placeholder_global_unrolled_iter_0[0], dtype="handle"))
        T.evaluate(T.call_extern("ethosu_copy", buffer_1[0], 112, placeholder_d_global_unrolled_iter_0[0], dtype="handle"))
        T.evaluate(T.call_extern("ethosu_conv2d", "int8", 16, 16, 32, 16, 0, 16, placeholder_5[0], 0, 0, 0, T.float32(0.5), 10, "NHWC", 512, 32, 1, "int8", 16, 16, 10, 16, 0, 16, ethosu_write_1[0], 0, 0, 0, T.float32(0.25), 14, "NHWC", 256, 16, 1, 1, 1, 1, 1, 1, 1, placeholder_global_unrolled_iter_0[0], 416, T.int8(-1), T.int8(-1), 12, placeholder_d_global_unrolled_iter_0[0], 112, T.int8(-1), T.int8(-1), 0, 0, 0, 0, "NONE", 0, 0, "TFL", "NONE", 0, 0, 0, dtype="handle"))
        T.evaluate(T.call_extern("ethosu_copy", buffer_2[0], 272, placeholder_global_unrolled_iter_1[0], dtype="handle"))
        T.evaluate(T.call_extern("ethosu_copy", buffer_3[0], 64, placeholder_d_global_unrolled_iter_1[0], dtype="handle"))
        T.evaluate(T.call_extern("ethosu_conv2d", "int8", 16, 16, 32, 16, 0, 16, placeholder_5[0], 0, 0, 0, T.float32(0.5), 10, "NHWC", 512, 32, 1, "int8", 16, 16, 6, 16, 0, 16, ethosu_write_1[10], 0, 0, 0, T.float32(0.25), 14, "NHWC", 256, 16, 1, 1, 1, 1, 1, 1, 1, placeholder_global_unrolled_iter_1[0], 272, T.int8(-1), T.int8(-1), 12, placeholder_d_global_unrolled_iter_1[0], 64, T.int8(-1), T.int8(-1), 0, 0, 0, 0, "NONE", 0, 0, "TFL", "NONE", 0, 0, 0, dtype="handle"))
    __tvm_meta__ = None
# fmt: on


def test_weight_stream():
    def _cascader(cached_func, const_dict, sch):
        weight = cached_func.inputs[1]
        scale_bias = cached_func.inputs[2]
        out = cached_func.outputs[0]
        conv_compute = OperatorCompute.from_output(out)
        co = conv_compute.split(sch, 3, 10)
        cache_weight = sch.cache_read(weight, "global", [conv_compute.op])
        cache_scale_bias = sch.cache_read(scale_bias, "global", [conv_compute.op])
        sch[cache_weight].compute_at(sch[out], co)
        sch[cache_scale_bias].compute_at(sch[out], co)

    def _get_func():
        ifm = relay.var("ifm", shape=(1, 16, 16, 32), dtype="int8")
        conv = make_ethosu_conv2d(
            ifm,
            32,
            16,
            (1, 1),
            (0, 0),
            (1, 1),
            (1, 1),
        )
        func = relay.Function(relay.analysis.free_vars(conv), conv)
        func = run_opt_pass(func, relay.transform.InferType())
        return func

    func = _get_func()
    mod, _ = _lower_to_tir(func, cascader=_cascader)

    script = mod.script(show_meta=True)
    test_mod = tvm.script.from_source(script)
    reference_mod = WeightStream
    tvm.ir.assert_structural_equal(test_mod["main"], reference_mod["main"], True)


if __name__ == "__main__":
    pytest.main([__file__])
