# ThoughtTronix Codebase Map

## 1. Apps and What They Own

Accounts is in charge of the different types of users and what they can access. For example, customers can use the website to buy items, while employees can access things like product and stock information.

Products is in charge of the products, tags, and categories, along with the pages where customers can view the products.

Orders is in charge of the shopping cart, checkout, placing orders, and order confirmations.

Dashboard is in charge of the employee and staff analytics page and gathers information about store products and orders.

## 2. Path of a Request

When a customer goes to the home page /, it goes through config/urls.py, then products/urls.py, then to CatalogView. CatalogView then displays the products/catalog.html page.

## 3. Model I Read

There is one Cart model for each user, and the cart holds the customer's items. I found the total() method interesting because it automatically calculates the total price of the items in the cart.

## 4. Deleting a Category

If someone tries to delete a category while it still has products in it, the website will not let it happen. Products are protected from losing their category because of this code: category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")

## 5. Tests and Fixtures

The bulk of the tests are stored within the Django apps, like products/tests.py and accounts/tests.py. conftest.py holds shared pytest fixtures that create test data like categories, staff users, and customers so the tests can use them.

## 6. Something I Am Still Working to Understand

I was unsure about how the website handles stock and which items are in stock or out of stock. I asked the agent about it, and the agent helped me understand that the website uses the is_available setting to determine whether a product is available.