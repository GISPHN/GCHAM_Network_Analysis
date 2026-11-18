def classFactory(iface):
    from .accessibility import AccessibilityPrototypePlugin
    return AccessibilityPrototypePlugin(iface)
