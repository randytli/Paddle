#   Copyright (c) 2018 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import unittest
import numpy as np
from op_test import OpTest
import paddle.fluid.core as core
import paddle.fluid as fluid
from paddle.fluid import compiler, Program, program_guard
import paddle

np.random.seed(10)


def stable_softmax(x):
    """Compute the softmax of vector x in a numerically stable way."""
    # clip to shiftx, otherwise, when calc loss with
    # log(exp(shiftx)), may get log(0)=INF
    shiftx = (x - np.max(x)).clip(-64.)
    exps = np.exp(shiftx)
    return exps / np.sum(exps)


class TestSoftmaxOp(OpTest):
    def get_x_shape(self):
        return [10, 10]

    def get_axis(self):
        return -1

    def setUp(self):
        self.op_type = "softmax"
        self.use_cudnn = False
        self.use_mkldnn = False
        self.dtype = np.float64
        self.init_kernel_type()
        self.shape = self.get_x_shape()
        self.axis = self.get_axis()

        np.random.seed(0)
        x = np.random.uniform(0.1, 1, self.shape).astype(self.dtype)
        out = np.apply_along_axis(stable_softmax, self.axis, x)

        self.inputs = {'X': OpTest.np_dtype_to_fluid_dtype(x)}
        self.outputs = {'Out': out}
        self.attrs = {
            'axis': self.axis,
            'use_cudnn': self.use_cudnn,
            'use_mkldnn': self.use_mkldnn
        }

    def init_kernel_type(self):
        pass

    def test_check_output(self):
        # TODO(wangzhongpu): support mkldnn op in dygraph mode
        if self.use_cudnn:
            place = core.CUDAPlace(0)
            self.check_output_with_place(
                place, atol=1e-5, check_dygraph=(self.use_mkldnn == False))
        else:
            self.check_output(check_dygraph=(self.use_mkldnn == False))

    def test_check_grad(self):
        # TODO(wangzhongpu): support mkldnn op in dygraph mode
        if self.use_cudnn or self.dtype == np.float16:
            place = core.CUDAPlace(0)
            if core.is_float16_supported(place):
                self.check_grad_with_place(
                    place, ["X"],
                    "Out",
                    max_relative_error=0.01,
                    check_dygraph=(self.use_mkldnn == False))
        else:
            self.check_grad(
                ["X"],
                "Out",
                max_relative_error=0.01,
                check_dygraph=(self.use_mkldnn == False))


class TestSoftmaxOpError(unittest.TestCase):
    def test_errors(self):
        with program_guard(Program(), Program()):
            # The input type of softmax_op must be Variable.
            x1 = fluid.create_lod_tensor(
                np.array([[-1]]), [[1]], fluid.CPUPlace())
            self.assertRaises(TypeError, fluid.layers.softmax, x1)
            # The input dtype of softmax_op must be float16, float32 or float64.
            x2 = fluid.layers.data(name='x2', shape=[4], dtype="int32")
            self.assertRaises(TypeError, fluid.layers.softmax, x2)
            x3 = fluid.layers.data(name='x3', shape=[4], dtype="float16")
            fluid.layers.softmax(x3)


class TestSoftmaxOp2(TestSoftmaxOp):
    def get_x_shape(self):
        return [2, 3, 4, 5]


class TestSoftmaxOp3(TestSoftmaxOp):
    def get_x_shape(self):
        return [2, 3, 4, 5]

    def get_axis(self):
        return 0


class TestSoftmaxOp4(TestSoftmaxOp):
    def get_x_shape(self):
        return [2, 3, 4, 5]

    def get_axis(self):
        return 1


class TestSoftmaxOp5(TestSoftmaxOp):
    def get_x_shape(self):
        return [2, 3, 4, 5]

    def get_axis(self):
        return 2


class TestSoftmaxOp6(TestSoftmaxOp):
    def get_x_shape(self):
        return [2, 3, 4, 5]

    def get_axis(self):
        return 3


@unittest.skipIf(not core.is_compiled_with_cuda(),
                 "core is not compiled with CUDA")
class TestSoftmaxCUDNNOp(TestSoftmaxOp):
    def init_kernel_type(self):
        self.use_cudnn = True


@unittest.skipIf(not core.is_compiled_with_cuda(),
                 "core is not compiled with CUDA")
class TestSoftmaxCUDNNOp2(TestSoftmaxCUDNNOp):
    def get_x_shape(self):
        return [2, 3, 4, 5]


@unittest.skipIf(not core.is_compiled_with_cuda(),
                 "core is not compiled with CUDA")
class TestSoftmaxCUDNNOp5(TestSoftmaxCUDNNOp):
    def get_x_shape(self):
        return [2, 3, 4, 5]

    def get_axis(self):
        return 3


@unittest.skipIf(not core.is_compiled_with_cuda(),
                 "core is not compiled with CUDA")
class TestSoftmaxFP16Op(TestSoftmaxOp):
    def init_kernel_type(self):
        self.dtype = np.float16

    def test_check_output(self):
        if core.is_compiled_with_cuda():
            place = core.CUDAPlace(0)
            if core.is_float16_supported(place):
                self.check_output_with_place(place, atol=1e-3)

    # FIXME: If the x_shape is [10, 10], gradient failed.
    def test_check_grad(self):
        pass


@unittest.skip('disable TestSoftmaxFP16Op2')
class TestSoftmaxFP16Op2(TestSoftmaxOp):
    def init_kernel_type(self):
        self.dtype = np.float16

    def test_check_output(self):
        if core.is_compiled_with_cuda():
            place = core.CUDAPlace(0)
            if core.is_float16_supported(place):
                self.check_output_with_place(place, atol=1e-3)

    def get_x_shape(self):
        return [2, 3, 4, 5]

    def test_check_grad(self):
        pass


@unittest.skipIf(not core.is_compiled_with_cuda(),
                 "core is not compiled with CUDA")
class TestSoftmaxFP16CUDNNOp(TestSoftmaxOp):
    def init_kernel_type(self):
        self.use_cudnn = True
        self.dtype = np.float16

    def test_check_output(self):
        if core.is_compiled_with_cuda():
            place = core.CUDAPlace(0)
            if core.is_float16_supported(place):
                self.check_output_with_place(place, atol=1e-3)


@unittest.skipIf(not core.is_compiled_with_cuda(),
                 "core is not compiled with CUDA")
class TestSoftmaxFP16CUDNNOp2(TestSoftmaxFP16CUDNNOp):
    def get_x_shape(self):
        return [2, 3, 4, 5]


class TestNnFunctionalSoftmaxApi(unittest.TestCase):
    def setUp(self):
        self.place = paddle.CUDAPlace(0) if core.is_compiled_with_cuda(
        ) else paddle.CPUPlace()
        self.x_np = np.random.uniform(-1., 1., [2, 3, 4, 5]).astype('float32')
        self.out_ref = np.apply_along_axis(stable_softmax, -1, self.x_np)

    def test_api_static(self):
        train_program = Program()
        startup_program = Program()
        with program_guard(train_program, startup_program):
            x = paddle.data('X', self.x_np.shape, 'float32')
            out = paddle.nn.functional.softmax(x)

        exe = paddle.Executor(self.place)
        res = exe.run(train_program, feed={'X': self.x_np}, fetch_list=[out])

        assert np.allclose(self.out_ref, res[0])

    def test_api_imperative(self):
        with paddle.imperative.guard(self.place):
            x = paddle.imperative.to_variable(self.x_np)
            out = paddle.nn.functional.softmax(x)
            assert np.allclose(self.out_ref, out.numpy())

            out = paddle.nn.functional.softmax(x, axis=0)
            out_ref = np.apply_along_axis(stable_softmax, 0, self.x_np)
            assert np.allclose(out_ref, out.numpy())

    def test_error(self):
        with program_guard(Program(), Program()):
            # The x should be variable and its dtype should be float32, float64.
            self.assertRaises(TypeError, paddle.nn.functional.softmax, [1])

            x = paddle.data(name='x', shape=[2, 3], dtype='int32')
            self.assertRaises(TypeError, paddle.nn.functional.softmax, x)


if __name__ == "__main__":
    unittest.main()
