import spacy
nlp = spacy.load('en_core_web_sm')
from spacy import displacy

text = "chicken, breast or thigh"
#text = "@curry powder"
#text = "ground pork, chicken or turkey"
#text = "provolone"
#text = "salad greens of choice"
#text = "chicken, thigh or breast"
#text = "medium shrimp, peeled and deveined"
#text = "salt or pepper"
#text = "chicken (breast or thigh)"
# text = "chili garlic sauce or sambal olek "
# finely shredded or chopped cabbage 
# pineapple chunks in juice

# boneless, skinless chicken thighs 
# boneless skinless chicken thighs 
#text = "salad greens of choice"
text = "splash of oil"
# bone-in skin-on chicken pieces
text = "3/4 water"
text = "plain breadcrumbs"

from util import *
name = clean_name(text)
#name = gpt3_format_name(text)
print(name)
