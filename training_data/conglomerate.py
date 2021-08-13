import re

fo = open('sanitized_data.txt')
fo_ = open('training_data.txt', 'w')
try:
    text = fo.read()
    sentences = text.split('\n')
    
    for sentence in sentences:
        sentence = re.sub(r'\b(\w+)( \1\b)+', r'\1', sentence)
        fo_.write(sentence + ' ')

finally:
    fo.close()
    fo_.close()