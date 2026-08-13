from widgets.common.kig_text_tile import KiGTextTile


class CashCategoryTile(KiGTextTile):

    def __init__(self, category, callback=None, **kwargs):

        super().__init__(
            text=category["name"],
            data=category,
            callback=callback,
            **kwargs
        )