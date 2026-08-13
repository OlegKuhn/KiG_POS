from models.cart_item import CartItem


class Cart:
    """
    Verwaltet den Warenkorb.
    """

    def __init__(self):

        self.items = []

    # =====================================================
    # Warenkorb leeren
    # =====================================================

    def clear(self):

        self.items.clear()

    # =====================================================
    # Artikel hinzufügen
    #
    # Existiert der Artikel bereits im Warenkorb,
    # wird die Menge erhöht.
    # =====================================================

    def add(self, article):

        for item in self.items:

            if item.article.id == article.id:

                item.quantity += 1

                return item

        # -------------------------------------------------
        # Neue Position
        # -------------------------------------------------

        item = CartItem(article)

        self.items.append(item)

        return item

    # =====================================================
    # Bereits erzeugtes CartItem hinzufügen
    #
    # Wird z. B. beim Duplizieren verwendet.
    # Hier erfolgt keine Zusammenfassung.
    # =====================================================

    def add_item(self, cart_item):

        self.items.append(cart_item)

        return cart_item

    # =====================================================
    # Position entfernen
    # =====================================================

    def remove(self, cart_item):

        if cart_item in self.items:

            self.items.remove(cart_item)

    # =====================================================
    # Prüfen, ob Position enthalten ist
    # =====================================================

    def contains(self, cart_item):

        return cart_item in self.items

    # =====================================================
    # Gesamtbetrag
    # =====================================================

    def total(self):

        return sum(
            item.total_price
            for item in self.items
        )