# -*- coding: utf-8 -*-
"""
    This script initializes the plugin, making it known to QGIS.
"""


def classFactory(iface):
    from .DEGURBA import DEGURBA_Plugin
    return DEGURBA_Plugin(iface)
