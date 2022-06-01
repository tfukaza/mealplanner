from typing import Text
from unicodedata import category
from bs4 import BeautifulSoup
import requests

import time

from rich import print
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from rich.text import Text
from rich.columns import Columns
from rich.prompt import Prompt

import json

import spacy
nlp = spacy.load('en_core_web_sm')

catergory_url = [
    "https://www.budgetbytes.com/category/recipes/global/italian/",
    "https://www.budgetbytes.com/category/recipes/global/asian/",
    "https://www.budgetbytes.com/category/recipes/global/indian/",
    "https://www.budgetbytes.com/category/recipes/global/mediterranean/",
    "https://www.budgetbytes.com/category/recipes/global/southwest/",
    "https://www.budgetbytes.com/category/recipes/meat/chicken/",
    "https://www.budgetbytes.com/category/recipes/meat/beef/",
    "https://www.budgetbytes.com/category/recipes/meat/pork/",
    "https://www.budgetbytes.com/category/recipes/meat/turkey/",
    "https://www.budgetbytes.com/category/recipes/meat/seafood/",
    "https://www.budgetbytes.com/category/recipes/pasta/",
    "https://www.budgetbytes.com/category/recipes/one-pot/",
    "https://www.budgetbytes.com/category/recipes/quick/",
    "https://www.budgetbytes.com/category/recipes/slow-cooker/",
    "https://www.budgetbytes.com/category/recipes/soup/",
    "https://www.budgetbytes.com/category/recipes/vegetarian/vegan/",
    "https://www.budgetbytes.com/category/recipes/cost-per-recipe/recipes-under-10/",
]

# clear_phrases = [
#     "to taste",
#     "any shape",
#     "extra virgin",
#     "all purpose", 
#     "freshly ground",
#     "all-purpose",
# ]

# clear_char = [
#     ",",
#     "*",
# ]

# categorizer = [
#     (["chicken thigh", "chicken thighs", "boneless skinless chicken thighs"], "chicken thigh"),
#     (["chicken breast", "chicken breasts", "boneless skinless chicken breasts", "boneless skinless chicken breast"], "chicken breast"),
#     (["garlic", "garlic cloves", "cloves garlic"], "garlic"),
#     (["onion", "onions"], "onion"),
#     (["egg", "eggs"], "egg"),
#     (["black pepper", "pepper"], "pepper"),
#     ([  "non stick spray as needed", 
#         "non stick spray", 
#         "as needed non stick spray",
#         "cooking oil",
#         "salad greens of choice",
#         ], "EXCLUDE"),
# ]

# compacter = [
#     (["chicken"], ["broth", "stock"], "chicken"),
#     (["beef"], ["broth", "stock"], "beef"),
# ]


# multi_names = [
#     ["salt", "pepper"]
# ]



def scrape_recipe():
    db = {}
    for url in catergory_url:
        i = 1
        while True:
            req_url = f'{url}page/{str(i)}/'
            i+=1
            print(req_url)
            response = requests.get(req_url)
            if response is None:
                print("[Red] Error: Could not connect to website")
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            content = soup.find("div", {"id": "content"})
            articles = content.findAll("article")

            if len(articles) == 0:
                break
            # for each article...
            for article in articles:
                # Get the a tag in post image div
                link = article.find("div", {"class": "post-image"}).find("a")
                # Get the href attribute
                href = link.get("href")
                print(href)
                response = requests.get(href)
                if response is None:
                    print("[Red] Error: Could not connect to article")
                    continue
                soup = BeautifulSoup(response.text, "html.parser")
                recipe_name = soup.find("h2", {"class": "wprm-recipe-name"})
                if recipe_name is None:
                    continue
                recipe_name = recipe_name.text
                ingredients = soup.find("div", {"class": "wprm-recipe-ingredients-container"})
                ingredients = ingredients.findAll("li")
                r_table = Table(title="Ingredients")
                r_table.add_column("Quantity")
                r_table.add_column("Unit")
                r_table.add_column("Name")
                #r_table.add_column("Cleaned Name")
                entry = {
                    "name": recipe_name,
                    "href": href,
                    "ingredients": []
                }
                for ing in ingredients:
                    amount = ing.find("span", {"class": "wprm-recipe-ingredient-amount"})
                    amount = amount.text if amount else ""
                    unit = ing.find("span", {"class": "wprm-recipe-ingredient-unit"})
                    unit = unit.text if unit else ""
                    name = ing.find("span", {"class": "wprm-recipe-ingredient-name"})
                    name = name.text if name else ""
                    #c_name = clean_name(name)
                    ing_tup = (amount, unit, name)
                    r_table.add_row(*ing_tup)
                    entry["ingredients"].append({
                        "amount": amount,
                        "unit": unit,
                        "name": name,
                        #"c_name": c_name
                    })
                r_panel = Panel(r_table, title=recipe_name, expand=False)
                print(r_panel)
                db[recipe_name] = entry
    
    with open("db.json", "w") as f:
        # convert db to json
        f.write(json.dumps(db))

exclude_list = {
    "salt",
    "pepper",
    "sugar",
    "olive oil",
    "flour",
    "water",
    "vegetable oil",
    "garlic",
    "butter",
    "EXCLUDE",
}

from util import clean_name

def format_recipe():
    with open("db.json", "r") as f:
        db = json.loads(f.read())
    
    fmt = {}
    cnt_ok = 0
    cnt_nr = 0
    unrecognized = []
    r = []
    for recipe in db.values():
        fmt_ing = []
        recipe_data = {
            "name": recipe["name"],
            "link": recipe["href"],
            "ingredients": []
        }
        ings = []
        all_ing_parsed = True
        for ing in recipe["ingredients"]:
            names = clean_name(ing["name"])
            if not names:
                cnt_nr += 1
                unrecognized.append(ing["name"])
                all_ing_parsed = False
                continue
            amount = ing["amount"]
            unit = ing["unit"]
            cnt_ok += 1
            fmt_ing.extend(names)
            ings.append((amount, unit, names))
        # for i in fmt_ing:
        #     if i in exclude_list:
        #         fmt_ing.remove(i)
        # fmt_ing = [i for i in fmt_ing if i not in exclude_list]
        if all_ing_parsed:
            recipe_data["ingredients"] = ings
            r.append(recipe_data)
        fmt[recipe["name"]] = {
            "href": recipe["href"],
            "ingredients": fmt_ing   
        }
    
    print(f"{cnt_ok}/{cnt_nr + cnt_ok}: %{(cnt_ok*100)/(cnt_nr + cnt_ok):.4f}")
    # Sort the unrecognized ingredients by frequency
    from collections import Counter
    unrecognized = Counter(unrecognized)
    unrecognized = sorted(unrecognized.items(), key=lambda x: x[1], reverse=True)
    print(f"Unrecognized ingredients (most frequent first):")
    for i in unrecognized[:10]:
        print(f"{i[0]} ({i[1]})")
 
 
        
    with open("db1.json", "w") as f:
        f.write(json.dumps(fmt))
    with open("recipes.json", "w") as f:
        f.write(json.dumps(r))

def process_ingredients():
    with open("db1.json", "r") as f:    
        db = json.load(f)
    
    def count_ing(count, name):
        if name not in count:
            count[name] = 1
        else:
            count[name] += 1

    # analyze which ingredients are most common
    # for each recipe...
    count = {}
    for recipe in db.values():
        # for each ingredient...
        for ing in recipe["ingredients"]:
            count_ing(count, ing)
    
    # Sort count by number of times ingredient is used
    count = sorted(count.items(), key=lambda x: x[1], reverse=False)
    #print(count)
    
    with open("db2.json", "w") as f:
        count = {"data": count}
        f.write(json.dumps(count))

have = {
    "dried basil",
    "dried oregano",
    "italian seasoning",
    "brown sugar",
    "garlic",
    "balsamic vinegar",
    "milk",
    "onion powder",
    "garlic powder",
    "salt",
    "pepper",
    "dijon mustard",
    "mayonnaise",
    "cumin",
    "soy sauce",
    "honey",
    "egg",
    "cornstarch",
}

def process_ingredients2():
    thresh = 1.1
    ing_thresh = 30
    missing_thresh = 1
    with open("db1.json", "r") as f:
        recipes = json.load(f)
    with open("db2.json", "r") as f:
        count = json.load(f)["data"]
    
    total_recipes = len(recipes)

    for rec in recipes.values():
        rec["ing_count"] = len(rec["ingredients"])

    recipe_make = []
    needed_ing = []
    
    count = sorted(count, key=lambda x: x[1], reverse=True)
    ing_cnt = 0
    for ing in count:
        name = ing[0]
        if not name in have:
            ing_cnt+=1
            needed_ing.append(name)
        for n, rec in recipes.items():
            r_ing = rec["ingredients"]
            if name in r_ing and len(r_ing) > missing_thresh:
                r_ing.remove(name)
                if len(r_ing) <= missing_thresh:
                    recipe_make.append([n, r_ing, rec["href"]])
        
        if len(recipe_make)/total_recipes >= thresh:
            break
        if ing_cnt >= ing_thresh:
            break
    
    for rec in recipe_make:
        rec[1] = [i for i in rec[1] if i not in have]    
    have_txt = "\n".join(have)
    have_panel = Panel(have_txt, title=f"Have({len(have)})", expand=False)
    needed_txt = "\n".join(needed_ing)
    needed_panel = Panel(needed_txt, title=f"Need({len(needed_ing)})", expand=False)
    ing_col = Columns()
    ing_col.add_renderable(have_panel)
    ing_col.add_renderable(needed_panel)

    make_table = Table()
    make_table.add_column("Recipe")
    make_table.add_column("Missing")
    make_table.add_column("Link")
   
    for rec in recipe_make:
        make_table.add_row(rec[0], " ".join(rec[1]), rec[2])

    make_panel = Panel(make_table, title=f"Make({len(recipe_make)})", expand=False)
    ing_col.add_renderable(make_panel)
    print(ing_col)   

    with open("db3.json", "w") as f:
        count = {"needed": needed_ing, "makes": recipe_make}
        f.write(json.dumps(count))

def main(): 
    #scrape_recipe()
    format_recipe()
    process_ingredients()
    process_ingredients2()

if __name__ == "__main__":
    main()