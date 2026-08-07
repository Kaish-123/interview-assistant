from collections import defaultdict


categories = [
    ["Electronics", "Computers"],
    ["Electronics", "Phones"],
    ["Computers", "Laptops"],
    ["Computers", "Desktops"],
    ["Phones", "Smartphones"],
    ["Phones", "Accessories"],
]

listings = [
    ["Dell", "Laptops"],
    ["Lenovo", "Laptops"],
    ["HP", "Computers"],
    ["Apple", "Electronics"],
    ["Samsung", "Smartphones"],
    ["Anker", "Accessories"],
]


def findBrandsInCategory(category, categories=categories, listings=listings):
    children = defaultdict(list)
    for parent, child in categories:
        children[parent].append(child)

    brands_by_category = defaultdict(list)
    for brand, cat in listings:
        brands_by_category[cat].append(brand)

    result = []
    seen = set()

    def visit(cat):
        for brand in brands_by_category[cat]:
            if brand not in seen:
                seen.add(brand)
                result.append(brand)
        for child in children[cat]:
            visit(child)

    visit(category)
    return result


if __name__ == "__main__":
    tests = {
        "Laptops": ["Dell", "Lenovo"],
        "Computers": ["HP", "Dell", "Lenovo"],
        "Electronics": ["Apple", "HP", "Dell", "Lenovo", "Samsung", "Anker"],
        "Desktops": [],
        "Phones": ["Samsung", "Anker"],
    }

    for category, expected in tests.items():
        actual = findBrandsInCategory(category)
        status = "PASS" if actual == expected else "FAIL"
        print(f"{status}: findBrandsInCategory({category!r}) -> {actual}")
