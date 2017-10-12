from . import HaloProperties

class Contamination(HaloProperties):

    def calculate(self, halo, exist):
        n_heavy = (halo.dm['mass'] > self.min_dm_mass).sum()
        return float(n_heavy) / len(halo.dm)

    def preloop(self, sim, filename, property_array):
        self.min_dm_mass = sim.dm['mass'].min()

    @classmethod
    def name(self):
        return "contamination_fraction"