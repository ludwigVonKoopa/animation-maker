import numpy as np
import pytest

import anim.path


class Test_TimePath:
    def test_setup(self):
        tp = anim.path.TimePath((0, 0), 0, 0, np.datetime64("now"))

    def test_wrong_time_init_1(self):
        """fail because t0 should be np.datetime64"""

        with pytest.raises(TypeError):
            tp = anim.path.TimePath((0, 0), 0, 0, t0=0)

    def test_wrong_time_init_2(self):
        """fail because t0 should be np.datetime64"""

        with pytest.raises(TypeError):
            tp = anim.path.TimePath((0, 0), 0, 0, np.timedelta64(5, "s"))

    def test_wrong_time_move_1(self):
        """fail because time should be np.datetime64"""
        tp = anim.path.TimePath((0, 0), 0, 0, np.datetime64("now"))

        with pytest.raises(TypeError):
            tp.move(0, (1, 1))

    def test_wrong_coords_init_1(self):
        """fail because coords should be tuple"""

        with pytest.raises(TypeError):
            tp = anim.path.TimePath(set(), 0, 0, np.datetime64("now"))

    def test_wrong_time_compute(self):
        """fail because time specified is before last time"""

        tp = anim.path.TimePath((0, 0), 0, 0, np.datetime64("now"))

        with pytest.raises(Exception):
            tp.move(np.datetime64("now") - np.timedelta64(15, "s"), (1, 1))

    def test_time_1(self):
        """test time interpolation"""

        t0 = np.datetime64("2024-01-01T01:11:01")
        tp = anim.path.TimePath((0, 0), 0, 0, t0)
        tp.move(np.timedelta64(1), (0, 0))
        tp.move(np.timedelta64(6), (0, 0))
        times, _ = tp.compute_path(np.timedelta64(1))

        ref = np.arange(t0, t0 + np.timedelta64(7))
        np.testing.assert_array_equal(times, ref)

    def test_time_2(self):
        """test time interpolation"""

        t0 = np.datetime64("2024-01-01T01:11:01")
        tp = anim.path.TimePath((0, 0), 0, 0, t0)
        tp.move(np.timedelta64(1), (0, 0))
        tp.move(np.timedelta64(6), (0, 0))
        times, _ = tp.compute_path(np.timedelta64(1, "h"))

        ref = np.arange(t0, t0 + np.timedelta64(7), np.timedelta64(1, "h"))
        np.testing.assert_array_equal(times, ref)

    def test_path_with_no_moving(self):
        """test path empty"""

        t0 = np.datetime64("2024-01-01T01:11:01")
        tp = anim.path.TimePath((0, 0), 0, 0, t0)
        tp.move(np.timedelta64(1), (0, 0))
        tp.move(np.timedelta64(6), (0, 0))
        _, extents = tp.compute_path(np.timedelta64(1))

        ref = np.zeros((7, 4))
        np.testing.assert_array_equal(extents, ref)

    def test_path_with_simple_moving(self):
        t0 = np.datetime64("2024-01-01T03:10:05")
        tp = anim.path.TimePath((0, 0), 1, 1, t0)
        tp.move(np.timedelta64(1, "D"), (0, 24))
        tp.move(np.timedelta64(2, "D"), (48, 24))
        tp.move(np.timedelta64(1, "D"))
        _, extents = tp.compute_path(np.timedelta64(1, "h"))

        np.testing.assert_array_equal(extents[0], np.array([-1, 1, -1, 1]))
        np.testing.assert_array_equal(extents[24], np.array([-1, 1, 23, 25]))
        np.testing.assert_array_equal(extents[72], np.array([47, 49, 23, 25]))

    def test_path_with_simple_zooming(self):
        t0 = np.datetime64("2024-01-01T03:10:05")
        tp = anim.path.TimePath((0, 0), 1, 1, t0)
        tp.move_and_zoom(np.timedelta64(1, "D"), zoom=2)
        tp.move_and_zoom(np.timedelta64(1, "D"), zoom=4)
        tp.move(np.timedelta64(1, "D"))
        times, extents = tp.compute_path(np.timedelta64(1, "h"))

        ref = np.arange(t0, t0 + np.timedelta64(3, "D"), np.timedelta64(1, "h"))
        np.testing.assert_array_equal(times, ref)


class Test_FramePath:
    def test_setup(self):
        tp = anim.path.FramePath((0, 0), 0, 0)

    def test_wrong_coords_init_1(self):
        """fail because coords should be tuple"""

        with pytest.raises(TypeError):
            tp = anim.path.FramePath(set(), 0, 0)

    def test_wrong_time_move_1(self):
        """fail because time specified is before last time"""

        tp = anim.path.FramePath((0, 0), 0, 0)

        with pytest.raises(Exception):
            tp.move(np.datetime64("now") - np.timedelta64(15, "s"))

    def test_wrong_time_move_2(self):
        """fail because time specified is before last time"""

        tp = anim.path.FramePath((0, 0), 0, 0)

        with pytest.raises(Exception):
            tp.move(0)

    def test_path_with_simple_moving(self):
        tp = anim.path.FramePath((0, 0), 1, 1)
        tp.move(10, (0, 24))
        tp.move(20, (48, 24))
        tp.move(10)
        _, extents = tp.compute_path()

        np.testing.assert_array_equal(extents[0], np.array([-1, 1, -1, 1]))
        np.testing.assert_array_equal(extents[10], np.array([-1, 1, 23, 25]))
        np.testing.assert_array_equal(extents[30], np.array([47, 49, 23, 25]))
