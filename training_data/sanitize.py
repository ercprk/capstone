#!/usr/bin/python3

import os
import nltk
import re
import html
import spacy
#nltk.download('words')

def sanitize(text):
    res = ''
    words = set(nltk.corpus.words.words())
    nlp = spacy.load("en_core_web_lg")

    # Remove extra whitespaces
    sanitized = re.sub(r'\s+', ' ', text)

    # Remove web URLs
    sanitized = re.sub(r"http\S+", "", sanitized)

    # Remove HTML tags
    sanitized = re.sub('<[^<]+?>', '', sanitized)

    sentences = nltk.sent_tokenize(sanitized)
    for sentence in sentences:
        if is_stop_sentence(sentence):
            continue

        doc = nlp(sentence)
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                sentence.replace(ent.text, 'BUSINESS_NAME')
        
        res += sentence + '\n'
    
        #print(token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.shape_, token.is_alpha, token.is_stop)

    return res

def is_stop_sentence(sentence):
    words = set(['Copyright'])

    tokens = nltk.word_tokenize(sentence)
    for token in tokens:
        if token in words:
            return True

    return False

def main():

    # Filepaths
    original_filename = "unsanitized_data.txt"
    sanitized_filename = "sanitized_data.txt"

    # Read unsanitized, original data
    original_file = open(original_filename)
    try:
        text = original_file.read()
    finally:
        original_file.close()

    # Sanitize
    text = sanitize(text)

    # Write the result
    try:
        sanitized_file = open(sanitized_filename, "w")
        sanitized_file.write(text)
    finally:
        sanitized_file.close()

if __name__ == '__main__':
    main()
