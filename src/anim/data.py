from dataclasses import dataclass, field

import numpy as np
import pandas
import xarray as xr
import zarr

from anim.tools import Timing


@dataclass
class Stats:
    img_name: str = None  # filled in `process`
    img_building: float = np.nan  # filled in `process`
    img_saving: float = np.nan  # filled in `process`
    time_data_compress: float = np.nan  # filled in `dump_data`
    time_data_uncompress: float = np.nan  # filled in `load_data`
    time_data_computation: float = np.nan  # filled in `animate`
    size_data_uncompressed: float = np.nan  # filled in `dump_data`
    size_data_compressed: float = np.nan  # filled in `dump_data`

    def __or__(self, other):
        stat = Stats()
        stat.img_name = other.img_name if other.img_name is not None else self.img_name
        for k, v in other.__dict__.items():
            if k == "img_name":
                continue

            if not np.isnan(v):
                setattr(stat, k, v)
            else:
                setattr(stat, k, getattr(self, k))
        return stat

    def to_dict(self):
        return self.__dict__

    def __str__(self):
        msg = []
        data = []
        # data=(compute=2500ms, size=3Mo->2Mo(250.02ms)|image=(build=250ms,save=350ms)

        # normally, this one is always setup
        if not np.isnan(self.time_data_computation):  # is not None:
            # msg = msg + f", compute={self.time_data_computation*1e3:.2f}ms"
            data.append(f"compute={self.time_data_computation*1e3:6.2f}ms")

        # normally, this one is always setup
        if not np.isnan(self.size_data_uncompressed):  # is not None:
            # msg = msg + f"size {self.size_data_uncompressed/1e6:.2f}Mo"
            data.append(f"size={self.size_data_uncompressed/1e3:6.2f}Ko")

        if not np.isnan(self.size_data_compressed):  # is not None:
            # msg = msg + f"->{self.size_data_compressed/1e6:.2f}Mo"
            data[-1] += f"->{self.size_data_compressed/1e3:6.2f}Ko"

        if not np.isnan(self.time_data_compress):  # is not None:
            # msg = msg + f", compress={self.time_data_compress*1e3:.2f}ms"
            data[-1] += f"[{self.time_data_compress*1e3:6.2f}ms]"

        msg_data = ",".join(data)
        msg_data = f"data=({msg_data})"
        msg.append(msg_data)

        img = []
        if not np.isnan(self.img_building):  # is not None:
            img.append(f"build={self.img_building*1e3:6.2f}ms")
        if not np.isnan(self.img_saving):  # is not None:
            img.append(f"save={self.img_saving*1e3:6.2f}ms")

        if len(img) > 0:
            msg_img = ",".join(img)
            msg_img = f"image=({msg_img})"
            msg.append(msg_img)

        msg = "|".join(msg)
        return msg


class StatStorage:
    def __init__(self):
        self.data = dict()

    def __call__(self, stat: Stats):
        img_name = stat.img_name
        if img_name not in self.data:
            self.data[img_name] = stat
        else:
            self.data[img_name] |= stat

    def __getitem__(self, stat):
        return self.data[stat.img_name]

    def build_dataframe(self):  # describe(self):
        df = pandas.DataFrame(list(x.to_dict() for x in self.data.values()))
        del df["img_name"]
        units = {}  # "img_name": "img_name"}
        for k in "size_data_uncompressed", "size_data_compressed":
            df[k] = df[k] / 1e6
            units[k] = f"{k[5:]} (Mo)"

        for k in ("time_data_compress", "time_data_uncompress", "time_data_computation"):
            df[k] = df[k] * 1e3
            units[k] = f"{k[5:]} (ms)"

        for k in ("img_building", "img_saving"):
            units[k] = f"{k[4:]} (s)"

        df.columns = [f"{units[k]}" for k in df.columns]
        return df

    @property
    def size(self):
        return len(self.data)


@dataclass
class AnimationInfo:
    imagePatern: str
    checkIfImageExist: bool = False
    onlyCompute: bool = False
    savefig_kwargs: dict = field(default_factory=dict)


def zarr_weight(group):
    "compute size of all variable contained in the group"
    return sum(group[var].nbytes_stored for var in group.array_keys())


def load_data(raw: xr.Dataset | zarr.hierarchy.Group):
    if isinstance(raw, zarr.hierarchy.Group):
        with Timing() as timing:
            ds = xr.open_zarr(raw.store, chunks=None).load()
            ds.attrs.update(raw.attrs)
        return ds, Stats(time_data_uncompress=timing.dt)

    return raw, Stats()


def dump_data(ds: xr.Dataset or zarr.hierarchy.Group, max_size=1e6, encoding: dict() or None = None):
    # if data is already compressed
    stats = Stats(size_data_uncompressed=ds.nbytes)

    if isinstance(ds, zarr.hierarchy.Group):
        stats.size_data_compressed = zarr_weight(ds)
        return ds, stats

    elif ds.nbytes > max_size:
        zg = zarr.group()
        with Timing() as timing:
            ds.to_zarr(zg._store, mode="w", encoding=encoding)

        stats.size_data_compressed = zarr_weight(zg)
        stats.time_data_compress = timing.dt
        return zg, stats
    else:
        return ds, stats
