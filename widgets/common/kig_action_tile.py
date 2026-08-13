from widgets.common.kig_text_tile import KiGTextTile


class KiGActionTile(KiGTextTile):

    def __init__(self, text, callback=None, **kwargs):

        super().__init__(
            text=text,
            data=text,
            callback=callback,
            **kwargs
        )