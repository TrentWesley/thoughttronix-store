# Reflection

## Featured Products

### Question 1

I checked Is featured on the admin page, which changes the product's is_featured value in products/models.py. The templates/products/catalog.html and templates/products/detail.html files check that value, and when it is true, they show the Featured badge.

### Question 2

To verify that the feature worked, I visited the catalog page and saw the Featured badges. Then I clicked on Seraphine and saw the Featured badge on its product detail page. Finally, I ran uv run pytest and all 166 tests passed.

### Question 3
One problem I ran into was when I opened Seraphine and SoulSear Mark II, the Is available box was checked, but for SoulSear Mark I it was unchecked. I was debating whether to check it so they would all be the same, but after looking into it, I decided to leave it unchecked and only change the Is featured setting.