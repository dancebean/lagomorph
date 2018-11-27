import torch
import numpy as np
import math

import lagomorph as lm

# This enables cuda error checking in lagomorph which causes kernels to
# synchronize, which is why it's disabled by default
lm.set_debug_mode(True)

from testing.utils import catch_gradcheck

np.random.seed(1)

res = 3 # which resolution to test
dims = [2,3] # which dimensions to test
channels = [1,2,4] # numbers of channels to test
batch_sizes = [1,2] # which batch sizes to test

def test_affine_interp_identity():
    for bs in batch_sizes:
        for dim in dims:
            for c in channels:
                imsh = tuple([bs,c]+[res]*dim)
                I = torch.randn(imsh, dtype=torch.float64, requires_grad=True).cuda()
                A = torch.zeros((bs,dim,dim), dtype=I.dtype, requires_grad=False).to(I.device)
                T = torch.zeros((bs,dim), dtype=I.dtype, requires_grad=False).to(I.device)
                for i in range(dim):
                    A[:,i,i] = 1
                IAT = lm.affine_interp(I, A, T)
                assert torch.allclose(IAT, I), \
                        f"Affine interp by identity is non-trivial with batch size {bs} dim {dim} channels {c}"
def test_affine_interp_gradcheck_I():
    for bs in batch_sizes:
        for dim in dims:
            for c in channels:
                imsh = tuple([bs,c]+[res]*dim)
                I = torch.randn(imsh, dtype=torch.float64, requires_grad=True).cuda()
                A = torch.randn((bs,dim,dim), dtype=I.dtype, requires_grad=False).to(I.device)
                T = torch.randn((bs,dim), dtype=I.dtype, requires_grad=False).to(I.device)
                foo = lambda Ix: lm.affine_interp(Ix, A, T)
                catch_gradcheck(f"Failed affine interp gradcheck with batch size {bs} dim {dim} channels {c}", foo, (I,))
def test_affine_interp_gradcheck_A():
    for bs in batch_sizes:
        for dim in dims:
            for c in channels:
                imsh = tuple([bs,c]+[res]*dim)
                I = torch.randn(imsh, dtype=torch.float64, requires_grad=False).cuda()
                A = torch.randn((bs,dim,dim), dtype=I.dtype, requires_grad=True).to(I.device)
                T = torch.randn((bs,dim), dtype=I.dtype, requires_grad=False).to(I.device)
                foo = lambda Ax: lm.affine_interp(I, Ax, T)
                catch_gradcheck(f"Failed affine interp gradcheck with batch size {bs} dim {dim} channels {c}", foo, (A,))
def test_affine_interp_gradcheck_T():
    for bs in batch_sizes:
        for dim in dims:
            for c in channels:
                imsh = tuple([bs,c]+[res]*dim)
                I = torch.randn(imsh, dtype=torch.float64, requires_grad=False).cuda()
                A = torch.randn((bs,dim,dim), dtype=I.dtype, requires_grad=False).to(I.device)
                T = torch.randn((bs,dim), dtype=I.dtype, requires_grad=True).to(I.device)
                foo = lambda Tx: lm.affine_interp(I, A, Tx)
                catch_gradcheck(f"Failed affine interp gradcheck with batch size {bs} dim {dim} channels {c}", foo, (T,))
def test_affine_interp_gradcheck_all():
    for bs in batch_sizes:
        for dim in dims:
            for c in channels:
                imsh = tuple([bs,c]+[res]*dim)
                I = torch.randn(imsh, dtype=torch.float64, requires_grad=True).cuda()
                A = torch.randn((bs,dim,dim), dtype=I.dtype, requires_grad=True).to(I.device)
                T = torch.randn((bs,dim), dtype=I.dtype, requires_grad=True).to(I.device)
                catch_gradcheck(f"Failed affine interp gradcheck with batch size {bs} dim {dim} channels {c}", lm.affine_interp, (I,A,T))

def test_affine_2d_match_3d():
    """Test that 2D matches 3D affine interpolation"""
    for bs in batch_sizes:
        for c in channels:
            with torch.no_grad():
                imsh = (bs,c,res,res)
                I2 = torch.randn(imsh, dtype=torch.float64).cuda()
                A2 = torch.randn((bs,2,2), dtype=torch.float64, device=I2.device)
                T2 = torch.randn((bs,2), dtype=A2.dtype, device=I2.device)
                I3 = I2.view(bs,c,res,res,1)
                A3 = torch.cat((
                    A2[:,0,0].unsqueeze(1),
                    A2[:,0,1].unsqueeze(1),
                    torch.zeros((bs,1), dtype=T2.dtype, device=I2.device),
                    A2[:,1,0].unsqueeze(1),
                    A2[:,1,1].unsqueeze(1),
                    torch.zeros((bs,3), dtype=T2.dtype, device=I2.device),
                    torch.ones((bs,1), dtype=T2.dtype, device=I2.device),
                    ),
                        dim=1).view(bs,3,3)
                T3 = torch.cat((T2, torch.zeros((bs,1), dtype=T2.dtype,
                    device=I2.device)), dim=1)
                J2 = lm.affine_interp(I2, A2, T2).view(bs,c,res,res,1)
                J3 = lm.affine_interp(I3, A3, T3)
                assert torch.allclose(J2, J3), f"Failed affine 2D==3D check with batch size {bs} channels {c}"

def test_affine_inverse():
    for bs in batch_sizes:
        for dim in dims:
            A = torch.randn((bs,dim,dim), dtype=torch.float64)
            T = torch.randn((bs,dim), dtype=A.dtype)
            x = torch.randn((bs,dim,1), dtype=T.dtype)
            Ainv, Tinv = lm.affine_inverse(A, T)
            y = torch.matmul(A, x) + T.unsqueeze(2)
            xhat = torch.matmul(Ainv, y) + Tinv.unsqueeze(2)
            assert torch.allclose(x, xhat), f"Failed affine inverse with batch size {bs} dim {dim}"
