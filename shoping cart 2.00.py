import json
import os


class Product:
    def __init__(self, product_id, name, price, quantity_available):
        self._product_id = product_id
        self._name = name
        self._price = price
        self._quantity_available = quantity_available

    @property
    def product_id(self): return self._product_id

    @property
    def name(self): return self._name

    @property
    def price(self): return self._price

    @property
    def quantity_available(self): return self._quantity_available

    @quantity_available.setter
    def quantity_available(self, value):
        self._quantity_available = max(0, value)

    def decrease_quantity(self, amount):
        if 0 < amount <= self._quantity_available:
            self._quantity_available -= amount
            return True
        return False

    def increase_quantity(self, amount):
        self._quantity_available += amount

    def display_details(self):
        return f"{self.product_id} | {self.name} | ₹{self.price} | Stock: {self.quantity_available}"

    def to_dict(self):
        return {
            "type": "base",
            "product_id": self._product_id,
            "name": self._name,
            "price": self._price,
            "quantity_available": self._quantity_available
        }


class PhysicalProduct(Product):
    def __init__(self, product_id, name, price, quantity_available, weight):
        super().__init__(product_id, name, price, quantity_available)
        self._weight = weight

    @property
    def weight(self): return self._weight

    def display_details(self):
        return f"{self.product_id} | {self.name} | ₹{self.price} | Stock: {self.quantity_available} | Weight: {self.weight}kg"

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "physical", "weight": self._weight})
        return data


class DigitalProduct(Product):
    def __init__(self, product_id, name, price, quantity_available, download_link):
        super().__init__(product_id, name, price, quantity_available)
        self._download_link = download_link

    @property
    def download_link(self): return self._download_link

    def display_details(self):
        return f"{self.product_id} | {self.name} | ₹{self.price} | Download: {self.download_link}"

    def to_dict(self):
        data = super().to_dict()
        data.update({"type": "digital", "download_link": self._download_link})
        return data


class CartItem:
    def __init__(self, product, quantity):
        self._product = product
        self._quantity = quantity

    @property
    def product(self): return self._product

    @property
    def quantity(self): return self._quantity

    @quantity.setter
    def quantity(self, value):
        self._quantity = max(0, value)

    def calculate_subtotal(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"Item: {self.product.name}, Qty: {self.quantity}, Price: ₹{self.product.price}, Subtotal: ₹{self.calculate_subtotal():.2f}"

    def to_dict(self):
        return {"product_id": self.product.product_id, "quantity": self.quantity}


class ShoppingCart:
    def __init__(self, product_catalog_file="products.json", cart_state_file="cart.json"):
        self._product_catalog_file = product_catalog_file
        self._cart_state_file = cart_state_file
        self._catalog = self._load_catalog()
        self._items = {}
        self._load_cart_state()

    def _load_catalog(self):
        if not os.path.exists(self._product_catalog_file):
            return {}
        with open(self._product_catalog_file, "r") as f:
            data = json.load(f)
            catalog = {}
            for prod in data:
                p_type = prod.get("type")
                if p_type == "physical":
                    obj = PhysicalProduct(
                        product_id=prod["product_id"],
                        name=prod["name"],
                        price=prod["price"],
                        quantity_available=prod["quantity_available"],
                        weight=prod["weight"]
                    )
                elif p_type == "digital":
                    obj = DigitalProduct(
                        product_id=prod["product_id"],
                        name=prod["name"],
                        price=prod["price"],
                        quantity_available=prod["quantity_available"],
                        download_link=prod["download_link"]
                    )
                else:
                    obj = Product(
                        product_id=prod["product_id"],
                        name=prod["name"],
                        price=prod["price"],
                        quantity_available=prod["quantity_available"]
                    )
                catalog[obj.product_id] = obj
            return catalog

    def _load_cart_state(self):
        if not os.path.exists(self._cart_state_file):
            return
        with open(self._cart_state_file, "r") as f:
            data = json.load(f)
            for item in data:
                product_id = item.get("product_id")
                if product_id and product_id in self._catalog:
                    prod = self._catalog[product_id]
                    self._items[product_id] = CartItem(prod, item["quantity"])

    def _save_catalog(self):
        with open(self._product_catalog_file, "w") as f:
            json.dump([prod.to_dict() for prod in self._catalog.values()], f, indent=4)

    def _save_cart_state(self):
        with open(self._cart_state_file, "w") as f:
            json.dump([item.to_dict() for item in self._items.values()], f, indent=4)

    def add_item(self, product_id, quantity):
        product = self._catalog.get(product_id)
        if product and product.quantity_available >= quantity:
            if product_id in self._items:
                self._items[product_id].quantity += quantity
            else:
                self._items[product_id] = CartItem(product, quantity)
            product.decrease_quantity(quantity)
            self._save_cart_state()
            return True
        return False

    def remove_item(self, product_id):
        if product_id in self._items:
            product = self._catalog[product_id]
            qty = self._items[product_id].quantity
            product.increase_quantity(qty)
            del self._items[product_id]
            self._save_cart_state()
            return True
        return False

    def update_quantity(self, product_id, new_quantity):
        if product_id in self._items:
            item = self._items[product_id]
            diff = new_quantity - item.quantity
            if diff > 0 and item.product.quantity_available >= diff:
                item.quantity = new_quantity
                item.product.decrease_quantity(diff)
                self._save_cart_state()
                return True
            elif diff < 0:
                item.quantity = new_quantity
                item.product.increase_quantity(-diff)
                self._save_cart_state()
                return True
        return False

    def get_total(self):
        return sum(item.calculate_subtotal() for item in self._items.values())

    def display_cart(self):
        print("\nYour Shopping Cart:")
        if not self._items:
            print("Cart is empty.")
            return
        for item in self._items.values():
            print(item)
        print(f"\nGrand Total: ₹{self.get_total():.2f}")

    def display_products(self):
        print("\nAvailable Products:")
        for product in self._catalog.values():
            print(product.display_details())


def main():
    cart = ShoppingCart()
    while True:
        print("\n===== Online Shopping Cart =====")
        print("1. View Products")
        print("2. Add Item to Cart")
        print("3. View Cart")
        print("4. Update Item Quantity")
        print("5. Remove Item from Cart")
        print("6. Checkout")
        print("7. Exit")
        choice = input("Enter choice (1-7): ")
        if choice == "1":
            cart.display_products()
        elif choice == "2":
            pid = input("Enter Product ID: ")
            try:
                qty = int(input("Enter Quantity: "))
                if cart.add_item(pid, qty):
                    print("Item added to cart.")
                else:
                    print("Failed to add item. Check ID or stock.")
            except:
                print("Invalid input.")
        elif choice == "3":
            cart.display_cart()
        elif choice == "4":
            pid = input("Enter Product ID: ")
            try:
                qty = int(input("Enter New Quantity: "))
                if cart.update_quantity(pid, qty):
                    print("Quantity updated.")
                else:
                    print("Update failed.")
            except:
                print("Invalid input.")
        elif choice == "5":
            pid = input("Enter Product ID: ")
            if cart.remove_item(pid):
                print("Item removed.")
            else:
                print("Item not found.")
        elif choice == "6":
            print(f"Checkout Total: ₹{cart.get_total():.2f}")
            print("Thank you for shopping.")
            break
        elif choice == "7":
            print("Exiting. Goodbye.")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
