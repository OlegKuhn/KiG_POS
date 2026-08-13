from models.article import Article


class CartItem:
    """
    Eine Position im Warenkorb.

    Der Artikel stammt aus dem Article-Modell.
    Preis und Menge werden für die Warenkorbposition
    separat gespeichert.
    """

    def __init__(self, article: Article):

        # =====================================================
        # Artikel
        # =====================================================

        self.article = article

        # =====================================================
        # Menge
        # =====================================================

        self.quantity = 1

        # =====================================================
        # Einzelpreis
        #
        # Der aktuelle Artikelpreis wird beim Hinzufügen
        # übernommen.
        #
        # Danach kann der Preis der Warenkorbposition
        # unabhängig vom Artikel verändert werden.
        # =====================================================

        self.unit_price = article.price

    # =========================================================
    # Gesamtpreis der Position
    # =========================================================

    @property
    def total_price(self):

        return (
            self.quantity
            * self.unit_price
        )

    # =========================================================
    # String
    # =========================================================

    def __repr__(self):

        return (
            f"CartItem("
            f"article='{self.article.name}', "
            f"quantity={self.quantity}, "
            f"unit_price={self.unit_price:.2f}"
            f")"
        )