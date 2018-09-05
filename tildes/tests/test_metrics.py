# Copyright (c) 2018 Tildes contributors <code@tildes.net>
# SPDX-License-Identifier: AGPL-3.0-or-later

from tildes.metrics import _COUNTERS, _HISTOGRAMS


def test_all_metric_names_prefixed():
    """Ensure all metric names have the 'tildes_' prefix."""
    for metric_dict in (_COUNTERS, _HISTOGRAMS):
        metrics = metric_dict.values()
        for metric in metrics:
            # this is ugly, but seems to be the "generic" way to get the name
            metric_name = metric.describe()[0].name

            assert metric_name.startswith("tildes_")
