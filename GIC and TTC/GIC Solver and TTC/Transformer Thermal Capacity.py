import numpy as np
import math
import pandas as pd

# critical data:
# gic flow
# Transformer type/data
# need to know windings, metallic parts oil
# move from this to XFMR thermal model
# get hot spot temperature
# Need to calculate effective gic on transformer

# "The effective GIC for a wye grounded
# delta transformer is equal to the GIC current flow through wye
# winding. However, in autotransformers and wye grounded-wye
# transformers both low and high side of the transformer pass the
# GIC. In this case, the transformer turn ratio should be considered
# to determine the reflection of the overall impact of dc current on
# both winding sides. Per phase effective GIC can be calculated
# using (6):
# ( )
# 3
# GIC NH L L
# effective H H H
# II I V
# I I I V
# α
# α
# +
# = = + − (6)
# where, HI and NI are the high-side and neutral dc current,
# respectively. HV is the rated voltage (rms) at high-voltage
# terminal. XV is the rated voltage (rms) at low-voltage terminal."

# Transformer thermal model equation
# define (2 tau / delta t) as alpha, tau is thermal time constant, delta t is change in time
# y(k+1) = (K / (1 + alpha))*(x(k) + x(k+1)) - ((1 - alpha)/(1 + alpha))*y(k)
# y(k + 1) = hot spot rise
# x(k) = past input temp
# x(k+1) = current temp
# K = steady-state temperature / input gic current
# K is dependant upon transformer model
# start by testing on one model
# choose a typical model/one in the case study used for gic solver program

#Total hotspot temperature must also account for top oil temperature
# THS = theta_TO + y(k +1)
# theta_TO = top oil temperature

