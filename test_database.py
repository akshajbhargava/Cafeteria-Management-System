from database import load_menu, update_stock

menu = load_menu()
print("Initial Menu:")
print(menu)

updated_menu = update_stock("Dal Chawal",1)
print("/nAfter Selling 1 plate Dal Chawal:")
print(updated_menu)

print("/ncsv saved in data/menu.csv")

<style> 

</style>