import spacy
from tomlkit import parse, dumps
nlp = spacy.load('en_core_web_sm')
from rich.prompt import Prompt

import openai
openai.api_key = ""

def gpt3_example(input, output):
    output = str(output)
    return f"Example: {input}\nOutput: {output}"

# Example: "skinless chicken, thigh or breast"
# Output: "chicken thigh", "chicken breast"
# Example: "ground pork, chicken, or beef" 
# Output: "ground pork", "ground chicken", "ground beef"
# Example: "skinless chicken breast"
# Output: "chicken breast"
# Example: "rice or apple cider vinegar" 
# Output: "rice vinegar", "apple cider vinegar"
# Example: "green onion, sliced"
# Output: "green onion"
examples = []
examples.append(gpt3_example("skinless chicken, thigh or breast", ["chicken thigh", "chicken breast"]))
examples.append(gpt3_example("ground pork, chicken, or beef", ["ground pork", "ground chicken", "ground beef"]))
examples.append(gpt3_example("rice or apple cider vinegar", ["rice vinegar", "apple cider vinegar"]))
examples.append(gpt3_example("dried fruit raisins, cranberries or chopped apricots", ["raisin", "cranberries", "apricots"]))
examples.append(gpt3_example("fresh ginger, grated or minced", ["ginger"]))
examples.append(gpt3_example("cubes bullion, vegetable, or chicken", ["vegtable bullion", "chicken bullion"]))
examples.append(gpt3_example("green onion, sliced", ["green onion"]))
examples.append(gpt3_example("skinless chicken breast", ["chicken breast"]))
examples.append(gpt3_example("chunk light tuna in water", ["tuna"]))
examples.append(gpt3_example("canned tomatoes", ["tomato"]))
examples.append(gpt3_example("3/4 water", ["water"]))
example_txt = "\n".join(examples) + "\n"

prompt_text = """
Convert the ingrideint written in plain English to an array of one or more strings.
Remove verbs and adjectives like "canned", "peeled", "large", "boneless", etc.\n
"""

# https://zestfuldata.com/pricing/

def gpt3_format_name(name):
    ask_text = f"""
    Input: {name}
    Output:
    """
    result = openai.Completion.create(
        engine="text-davinci-002",
        temperature=0, max_tokens=16,   
        prompt=prompt_text+example_txt+ask_text
    )

    result_text = result.choices[0].text
    result_list = result_text.strip()
    result_list = result_list.strip('][')
    result_list = result_list.replace("'", "")
    result_list = result_list.split(', ')
    return result_list


with open("words.toml", "r") as f:
    words_data = parse(f.read())
    valid_words = words_data["ingredients"]
    categorizer = words_data["categorizer"]
    valid = [v for k, v in valid_words.items()]
    valid = [i for j in valid for i in j]
    print(f"valid: {valid}")

with open("proc.toml", "r") as f:
    proc = parse(f.read())
    block_words = []
    for k, v in proc["block_word"].items():
        block_words.extend(v)
    print(f"block_words: {block_words}")
    block_phrases = []
    for k, v in proc["block_phrase"].items():
        block_phrases.extend(v)
    print(f"block_phrases: {block_phrases}")

def proc_conj(tokens):
    words = [[]]
    for token in tokens:
        if token.dep_ == "conj":
            words.append([token])
        elif token.dep_ != "cc":
            words[-1].append(token)
    return words

def remove_par(name):
    par_l = name.find("(")
    par_r = name.find(")")
    if par_l != -1 and par_r != -1:
        name = name[:par_l] + name[par_r+1:]
    return name

def to_lemma(words):
    #print(f"to_lemma: {tokens}")
    #words = [i for i in tokens if i.text not in block_words]
    return [i.lemma_ for i in words]

def proc_block_word(words):
    return [i for i in words if i.text not in block_words]

def split_by_conj(words):
    words = words.replace(" or", ":")
    words = words.replace(" and", ":")
    words = words.replace(" with", ":")
    words = words.replace(" of", ":")
    words = words.replace(" in", ":")
    words = words.replace(" &", ":")
    words = words.split(":")
    return words

def noun_to_singular(words):
    tokens = nlp(words)
    singular_words = []
    for token in tokens:
        if token.pos_ == "NOUN":
            singular_words.append(token.lemma_)
        else:
            singular_words.append(token.text)
    return " ".join(singular_words)

def remove_punct(noun):
    trans = str.maketrans('', '', '!"#$%&\'()*+,./:;<=>?@[\\]^_`{|}~')
    return nlp(noun.text.translate(trans))


def prompt_classification(name, post_fmt):

    # def add_valid(name, catergory):
    #     valid.append(name)
    #     if catergory in valid_words:
    #         valid_words[catergory].append(name)
    #     else:
    #         valid_words[catergory] = [name]
        
     # Ask the user what to do with this name
    print(f"{post_fmt}: not recognized. Original word was: {name}")
    return
    catergory = Prompt.ask(f"Enter a catergory for this:", default="etc")

    # add_valid = Prompt.ask("Add this name to the valid ingridients?", default="y")
    # if add_valid == "y":
    ret = []
    while True:
        n = Prompt.ask(f"[{len(ret)}] Enter a name for this item. Type '.' to end", default=post_fmt)
        if n == ".":
            break
        ret.append(n)
    
    if len(ret) == 0:
        return None
    
    for ing in ret:
        if ing not in valid:
            valid.append(ing)
        if catergory in valid_words:
            valid_words[catergory].append(ing)
        else:
            valid_words[catergory] = [ing]

    if len(ret) > 1:
        n = Prompt.ask(f"Enter the conjunction for this item:", default="and")
        ret = ret + [n]
        categorizer[name] = ret
    elif ret[0] != post_fmt:
        categorizer[name] = ret

    
    # if nam != name:
    #     categorizer[name] = nam
    #     with open("words.toml", "w") as f:
    #         write = {
    #             "ingredients": valid_words
    #             "categorizer": categorizer
    #         }
    #         f.write(dumps(write))
    with open("words.toml", "w") as f:
        write = {
            "ingredients": valid_words,
            "categorizer": categorizer
        }
        f.write(dumps(write))
    
    return ret

def proc_block_phrase(word):
    word = word.text
    for p in block_phrases:
        word = word.replace(p, "")
    return nlp(word)
        

def clean_name(name):
    #print(f"name_0: {name}")
    # All names must:
    # 1. be in lowercase
    # 2. have parentheses removed
    # 3. have leading and trailing spaces removed
    # 4. be in singular form
    # Don't lemmatize verbs to prevent cases like "powdered" being lemmatized to noun "powder",
    # making them indistinguishable from verb "powdered"
   
    name = remove_par(name)             # Remove parentheses
    name = name.lower()                 # Make lowercase
    name = name.replace("*", "")        
    name = name.replace("-", " ")
    name = name.replace(",", " ")
    name = name.strip()                 # Remove leading and trailing spaces

    for p in block_phrases:
        name = name.replace(p, "")
    #print(f"name_1: {name}")
    if name in categorizer:
        ing_list = categorizer[name]
        if len(ing_list) > 1:
            ing_list = ing_list[:-1]
        if any(ing not in valid for ing in ing_list):
            raise Exception(f"{name} is not a valid ingredient")
        return ing_list


    # If this is a known word, return it
    if name in valid:
        return [name]

    name = " ".join(n for n in name.split() if n not in block_words)
    name = noun_to_singular(name)
    #print(f"name_2: {name}")
    
    # Check if this is a known phrase, or a variant of a word
    if name in categorizer:
        ing_list = categorizer[name]
        if len(ing_list) > 1:
            ing_list = ing_list[:-1]
        if any(ing not in valid for ing in ing_list):
            raise Exception(f"{name} is not a valid ingredient")
        return ing_list
    
    

    # Convert name to a list of noun phrases
    tokens = name.split()
    cc = None
    ccs = [c for c in tokens if c in ["and", "or", "of", "in", "with", ",", "&"]]
    if len(ccs) > 0 or len(tokens) > 3:
        #print(f"name_1-a: {name}")
        ret = split_by_conj(name) if True else gpt3_format_name(name)
        nouns = [nlp(i) for i in ret]
        cc = ccs[0] if ccs else None
    else:
        # tokens = nlp(name)
        # nouns = list(tokens.noun_chunks)
        # if len(nouns) < 1:
        #     #print(f"name_1-b: {name}")
        nouns = [nlp(name)]

    #print(f"name_2: {list(nouns)}")
    ret = [remove_punct(noun) for noun in nouns]    # Remove punctuation
    #print(f"name_3: {ret}")
    #ret = [proc_block_phrase(noun) for noun in ret] # Remove phrases
    ret = [proc_block_word(i) for i in ret]         # Remove block words
    #print(f"name_4: {ret}")
    ret = [to_lemma(noun) for noun in ret]          # Lemmatize
    #print(f"name_5: {ret}")
    ret = [" ".join(i) for i in ret]                # Join back into a string
    ret = [i.strip() for i in ret]                  # Remove trailing spaces
    ret = [i for i in ret if i != ""]               # Remove empty tokens
    # Convert multiple whitespace to a single space
    ret = [" ".join(i.split()) for i in ret]
    # remove numbers
    for r in ret:
        if any(c.isdigit() for c in r):
            ret.remove(r)

    #print(f"name_6: {ret}")
    new_ret = []
    for r in ret:
        if name in categorizer:
            ing_list = categorizer[name]
            if len(ing_list) > 1:
                ing_list = ing_list[:-1]
            if any(ing not in valid for ing in ing_list):
                raise Exception(f"{name} is not a valid ingredient")
            new_ret.extend(ing_list)
        else:
            new_ret.append(r)

    for n in ret:
        if n not in valid:
            ret = prompt_classification(name, n)    
            break
    
    # if not ret or len(ret) == 0:
    #     pass
        #print(f"{name} is not a valid ingredient")
        #ret = prompt_classification(name, "")
    
    if not ret or len(ret) == 0:
        return None
    # If there was a conjunction, add it to the end of list
    if cc:
        ret.append(cc)
    return ret
