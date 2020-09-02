#!/usr/bin/env python3
import configargparse


SUPPRESS = configargparse.SUPPRESS


class ArgumentParser(configargparse.ArgumentParser):
    """Supports keys with underscores instead of dashes, for backwards compatibility
    with old paleomix config files, provided that these do not use per-host setions.
    """

    def get_possible_config_keys(self, *args, **kwargs):
        keys = super().get_possible_config_keys(*args, **kwargs)
        for key in keys:
            key = key.strip("-").replace("-", "_")
            if key not in keys:
                keys.append(key)

        return keys

    def convert_item_to_command_line_arg(self, action, key, value):
        # Ignore empty options from old config files
        if action and value == "=":
            return []

        return super().convert_item_to_command_line_arg(action, key, value)
