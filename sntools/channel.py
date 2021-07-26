#!/usr/bin/python

from math import pi, sin, cos, acos
import numpy as np
import random
from scipy import integrate, interpolate


def gen_evts(_channel, _flux, scale, seed, verbose):
    """Generate events.

    * Get event rate by interpolating from time steps in the input data.
    * For each 1ms bin, get number of events from a Poisson distribution.
    * Generate these events from time-dependent energy & direction distribution.

    Arguments:
    _channel -- BaseChannel instance for the current interaction channel
    _flux -- BaseFlux instance with appropriate flavor and time range
    scale -- constant factor, accounts for oscillation probability, distance of SN, size of detector
    seed -- random number seed to reproducibly generate events
    """
    random.seed(seed)
    np.random.seed(int(seed))

    global channel, cached_flux, flux
    flux = _flux
    channel = _channel
    tag = str(channel.__class__).split('.')[-2]

    # ddEventRate(eE, eNu, time) is called hundreds of times for each generated event,
    # often with identical eNu and time values (when integrating over eE).
    # To save time, we cache results in a dictionary.
    cached_flux = {}

    thr_e = 3.511  # detection threshold in HK: 3 MeV kinetic energy + rest mass

    # integrate over eE and then eNu to obtain the event rate at time t
    raw_nevts = [scale * integrate.nquad(ddEventRate, [channel.bounds_eE, channel.bounds_eNu], args=[t], opts=[channel._opts, {}])[0]
                 for t in flux.raw_times]
    event_rate = interpolate.pchip(flux.raw_times, raw_nevts)

    bin_width = 1  # in ms
    n_bins = int((flux.endtime - flux.starttime) / bin_width)  # number of full-width bins; int() implies floor()
    if verbose:
        print(f"[{tag}] Now generating events in {bin_width} ms bins from {flux.starttime} to {flux.endtime} ms")

    # scipy is optimized for operating on large arrays, making it orders of
    # magnitude faster to pre-compute all values of the interpolated functions.
    binned_t = [flux.starttime + (i + 0.5) * bin_width for i in range(n_bins)]
    binned_nevt_th = event_rate(binned_t)
    # check for unphysical values of interpolated function event_rate(t)
    for _i, _n in enumerate(binned_nevt_th):
        if _n < 0:
            binned_nevt_th[_i] = 0
    binned_nevt = np.random.poisson(binned_nevt_th)  # Get random number of events in each bin from Poisson distribution
    flux.prepare_evt_gen(binned_t)  # give flux script a chance to pre-compute values

    if verbose:  # compute events above threshold energy `thr_e`
        thr_bounds_eE = lambda _eNu, *args: [max(thr_e, channel.bounds_eE(_eNu)[0]), max(thr_e, channel.bounds_eE(_eNu)[1])]
        thr_raw_nevts = [scale * integrate.nquad(ddEventRate, [thr_bounds_eE, channel.bounds_eNu], args=[t], opts=[channel._opts, {}])[0]
                         for t in flux.raw_times]
        thr_event_rate = interpolate.pchip(flux.raw_times, thr_raw_nevts)
        thr_binned_nevt_th = thr_event_rate(binned_t)
        thr_nevt = sum(binned_nevt)

    events = []
    for i in range(n_bins):
        t0 = flux.starttime + i * bin_width

        if verbose and i % (10 ** (4 - verbose)) == 0:
            print(f"[{tag}] {t0}-{t0 + bin_width} ms: {binned_nevt[i]} events ({binned_nevt_th[i]:.5f} expected)")

        # generate events in this time bin
        for _ in range(binned_nevt[i]):
            eNu = get_eNu(binned_t[i])
            direction = get_direction(eNu)  # (dirx, diry, dirz)
            evt = channel.generate_event(eNu, *direction)
            evt.time = t0 + random.random() * bin_width
            events.append(evt)

            if verbose and evt.outgoing_particles[0][1] < thr_e:
                thr_nevt -= 1

    print(f"[{tag}] Generated {sum(binned_nevt)} particles (expected: {sum(binned_nevt_th):.2f} particles)")
    if verbose:
        print(f"[{tag}] -> above threshold of {thr_e} MeV: {thr_nevt} particles (expected: {sum(thr_binned_nevt_th):.2f})")
        print("**************************************")

    return events


# Helper functions
def ddEventRate(eE, eNu, time):
    """Double differential event rate."""
    if (eNu, time) not in cached_flux:
        cached_flux[(eNu, time)] = flux.nu_emission(eNu, time)
    return channel.dSigma_dE(eNu, eE) * cached_flux[(eNu, time)]


def rejection_sample(dist, min_val, max_val, n_bins=100):
    """Sample value from an arbitrary distribution."""
    p_max = 0
    j_max = 0
    bin_width = float(max_val - min_val) / n_bins

    # Iterative approach to speed up finding the maximum of `dist`.
    # Assumes that `dist` does not oscillate very quickly.
    # First, use coarse binning to find the approximate maximum:
    for j in range(0, n_bins, 10):
        val = min_val + bin_width * (j + 0.5)
        p = dist(val)
        if p > p_max:
            p_max = p
            j_max = j
    # Then, use finer binning around the approximate maximum.
    for j in range(max(j_max - 9, 0), min(j_max + 10, n_bins)):
        val = min_val + bin_width * (j + 0.5)
        p = dist(val)
        if p > p_max:
            p_max = p

    while True:
        val = min_val + (max_val - min_val) * random.random()
        if p_max * random.random() < dist(val):
            break

    return val


def get_eNu(time):
    """Get energy of interacting neutrino using rejection sampling."""
    dist = lambda _eNu: integrate.quad(
        ddEventRate, *channel.bounds_eE(_eNu), args=(_eNu, time), points=channel._opts(_eNu)["points"]
    )[0]
    eNu = rejection_sample(dist, *channel.bounds_eNu, n_bins=200)
    return eNu


def get_direction(eNu):
    """Get direction of outgoing particle using rejection sampling.
    (Assumes that incoming neutrino with energy eNu moves in z direction.)
    """
    dist = lambda _cosT: channel.dSigma_dCosT(eNu, _cosT)
    cosT = rejection_sample(dist, -1, 1, 200)
    sinT = sin(acos(cosT))
    phi = 2 * pi * random.random()  # randomly distributed in [0, 2 pi)
    return (sinT * cos(phi), sinT * sin(phi), cosT)
