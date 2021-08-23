import h5py
import numpy as np
from neutorch.cremi.volume import Volume


class CremiFile(object):

    def __init__(self, filename, mode):

        self.h5file = h5py.File(filename, mode)

        if mode == "w" or mode == "a":
            self.h5file["/"].attrs["file_format"] = "0.2"

    def __create_group(self, group):

        path = "/"
        for d in group.split("/"):
            path += d + "/"
            try:
                self.h5file.create_group(path)
            except ValueError:
                pass

    def __create_dataset(self, path, data, dtype, compression=None):
        """Wrapper around h5py's create_dataset. Creates the group, if not 
        existing. Deletes a previous dataset, if existing and not compatible. 
        Otherwise, replaces the dataset.
        """

        group = "/".join(path.split("/")[:-1])
        ds_name = path.split("/")[-1]

        self.__create_group(group)

        if ds_name in self.h5file[group]:

            ds = self.h5file[path]
            if ds.dtype == dtype and ds.shape == np.array(data).shape:
                print("overwriting existing dataset")
                self.h5file[path][:] = data[:]
                return

            del self.h5file[path]

        self.h5file.create_dataset(
            path, data=data, dtype=dtype, compression=compression)

    def write_volume(self, volume, ds_name, dtype):

        self.__create_dataset(ds_name, data=volume.data,
                              dtype=dtype, compression="gzip")
        self.h5file[ds_name].attrs["resolution"] = volume.resolution
        if volume.comment is not None:
            self.h5file[ds_name].attrs["comment"] = str(volume.comment)
        if tuple(volume.offset) != (0.0, 0.0, 0.0):
            self.h5file[ds_name].attrs["offset"] = volume.offset

    def read_volume(self, ds_name):

        volume = Volume(self.h5file[ds_name])

        volume.resolution = self.h5file[ds_name].attrs["resolution"]
        if "offset" in self.h5file[ds_name].attrs:
            volume.offset = self.h5file[ds_name].attrs["offset"]
        if "comment" in self.h5file[ds_name].attrs:
            volume.comment = self.h5file[ds_name].attrs["comment"]

        return volume

    def __has_volume(self, ds_name):

        return ds_name in self.h5file

    def write_raw(self, raw):
        """Write a raw volume.
        """

        self.write_volume(raw, "/volumes/raw", np.uint8)

    def write_neuron_ids(self, neuron_ids):
        """Write a volume of segmented neurons.
        """

        self.write_volume(neuron_ids, "/volumes/labels/neuron_ids", np.uint64)

    def write_clefts(self, clefts):
        """Write a volume of segmented synaptic clefts.
        """

        self.write_volume(clefts, "/volumes/labels/clefts", np.uint64)

    def has_raw(self):
        """Check if this file contains a raw volume.
        """
        return self.__has_volume("/volumes/raw")

    def has_neuron_ids(self):
        """Check if this file contains neuron ids.
        """
        return self.__has_volume("/volumes/labels/neuron_ids")

    def has_neuron_ids_confidence(self):
        """Check if this file contains confidence information about neuron ids.
        """
        return self.__has_volume("/volumes/labels/neuron_ids_confidence")

    def has_clefts(self):
        """Check if this file contains synaptic clefts.
        """
        return self.__has_volume("/volumes/labels/clefts")

    def read_raw(self):
        """Read the raw volume.
        Returns a Volume.
        """

        return self.read_volume("/volumes/raw")

    def read_neuron_ids(self):
        """Read the volume of segmented neurons.
        Returns a Volume.
        """

        return self.read_volume("/volumes/labels/neuron_ids")

    # def read_neuron_ids_confidence(self):
    #     """Read confidence information about neuron ids.
    #     Returns Confidences.
    #     """

    #     confidences = Confidences(num_levels=2)
    #     if not self.has_neuron_ids_confidence():
    #         return confidences

    #     data = self.h5file["/volumes/labels/neuron_ids_confidence"]
    #     i = 0
    #     while i < len(data):
    #         level = data[i]
    #         i += 1
    #         num_ids = data[i]
    #         i += 1
    #         confidences.add_all(level, data[i:i+num_ids])
    #         i += num_ids

    #     return confidences

    def read_clefts(self):
        """Read the volume of segmented synaptic clefts.
        Returns a Volume.
        """

        return self.read_volume("/volumes/labels/clefts")

    def close(self):

        self.h5file.close()