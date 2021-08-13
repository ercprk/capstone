#!/usr/bin/python3

import os
import nltk
import re
import html
import spacy
from commonregex import CommonRegex
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
#nltk.download('words')

def sanitize(text, sanitized_filename):

    # Remove web URLs
    sanitized = re.sub(r"http\S+", "", text)

    # Remove HTML tags
    sanitized = re.sub('<[^<]+?>', '', sanitized)

    # Remove HTML characters
    sanitized = re.sub('&[^ ]+;', '', sanitized)

    # Remove state abbreviations
    sanitized = re.sub('(?<!\w)(?:,\s+)?(?:A[LKZR]|C[AOT]|DE|FL|GA|HI|I[ADLN]|K[SY]|LA|M[EDAINSOT]|N[EVHJMYCD]|O[HKR]|PA|RI|S[CD]|T[NX]|UT|V[AT]|W[AIVY]),?\s?(?!\w)', '', sanitized)

    fo = open('unique_senders.txt')
    try:
        text_ = fo.read()
    finally:
        fo.close()

    # Load natural language processor and add custom organizations
    nlp = spacy.load("en_core_web_lg")
    ruler = nlp.add_pipe("entity_ruler")
    unique_senders = set(text_.split('\n'))
    patterns = list()
    for unique_sender in unique_senders:
        pattern = {"label": "ORG", "pattern": [{"LOWER": unique_sender}]}
        patterns.append(pattern)
    ruler.add_patterns(patterns)

    lemmatizer = WordNetLemmatizer()
    sentences = nltk.sent_tokenize(sanitized)
    counter = 0
    num_sentences = len(sentences)
    res = ''
    print('There are %d sentences' % (num_sentences))

    # Write the result
    try:
        sanitized_file = open(sanitized_filename, "w")
        for sentence in sentences:
            counter += 1
            if counter % 1000 == 0 or counter == num_sentences:
                print('%d sentences sanitized (%.2f%% complete)' % (counter, float(counter / num_sentences) * 100))

            if is_stop_sentence(sentence):
                continue

            #print('1 ' + sentence)
            doc = nlp(sentence)
            for ent in doc.ents:
                #print('ent: %s ent.label: %s' % (ent.text, ent.label_))
                if ent.label_ == 'ORG' or ent.label_ == 'NORP':
                    sentence = sentence.replace(ent.text, 'BUSINESSNAME')
                elif ent.label_ == 'PRODUCT':
                    sentence = sentence.replace(ent.text, 'PRODUCTNAME')
                elif ent.label_ == 'PERSON' and ent.label_ == 'GPE':
                    sentence = sentence.replace(ent.text, '')
                    
            #print('2 ' + sentence)
            # Remove times, dates, and prices
            parsed_text = CommonRegex(sentence)
            for price in parsed_text.prices:
                sentence = sentence.replace(price, '')

            #print('3 ' + sentence)
            # Remove non-dictionary words
            words = set(nltk.corpus.words.words())
            puncts = {'.', '"', "'", ',', '-', '%', '!', '?'}
            etcs = {'email', 'online'}
            words = words.union(puncts).union(etcs)
            tokens = nltk.wordpunct_tokenize(sentence)
            pos_tags = nltk.pos_tag(tokens)
            #print(pos_tags)

            for token_idx, token in enumerate(tokens):
                syntactic_category = get_syntactic_category(pos_tags[token_idx][1])
                if syntactic_category != None:
                    lemmatized_token = lemmatizer.lemmatize(token.lower(), syntactic_category)
                    #print('lemmatized: %s original: %s' % (lemmatized_token, token))
                    if lemmatized_token.lower() not in words and token != 'BUSINESSNAME' and token != 'PRODUCTNAME' and not token.isnumeric():
                        sentence = sentence.replace(token, '')
                else:
                    if token.lower() not in words and token != 'BUSINESSNAME' and token != 'PRODUCTNAME' and not token.isnumeric():
                        sentence = sentence.replace(token, '')

            #print('4 ' + sentence)

            # Remove extra whitespaces
            sentence = re.sub(r'\s+', ' ', sentence)
            sentence = re.sub(r' , ', ' ', sentence)
            sentence = re.sub(r' \.', '.', sentence)
            sentence = re.sub(r' !', '!', sentence)
            sentence = re.sub(r' \?', '?', sentence)
            #print('5 ' + sentence)

            sanitized_file.write(sentence + '\n')

    finally:
        sanitized_file.close()

def get_syntactic_category(pos_tag: str) -> str:
    if pos_tag.startswith('JJ'):
        return wordnet.ADJ
    elif pos_tag.startswith('NN'):
        return wordnet.NOUN
    elif pos_tag.startswith('RB'):
        return wordnet.ADV
    elif pos_tag.startswith('VB'):
        return wordnet.VERB
    else:
        return None

def is_stop_sentence(sentence):
    words = {'copyright', 'unsubscribe', 'instagram', 'twitter', 'facebook', 'youtube', 'style='}

    tokens = nltk.word_tokenize(sentence)
    for token in tokens:
        if token.lower() in words:
            return True

    parsed_text = CommonRegex(sentence)
    if len(parsed_text.street_addresses) > 0 or len(parsed_text.emails) > 0 or len(parsed_text.phones) > 0 or len(parsed_text.times) > 0 or len(parsed_text.dates) > 0 or len(parsed_text.links) > 0 or len(parsed_text.zip_codes) > 0:
        return True

    return False

def main():

    # Filepaths
    original_filename = "unsanitized_data.txt"

    # Read unsanitized, original data
    original_file = open(original_filename)
    try:
        text = original_file.read()
    finally:
        original_file.close()

    # Sanitize
    sanitize(text, "sanitized_data.txt")

if __name__ == '__main__':
    main()
