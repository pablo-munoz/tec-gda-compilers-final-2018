import re
import logging
import nltk

logger = logging.getLogger(__file__)

# Regular expression to separate the paragraphs of the input
# text into separate strings.
paragraph_regex = re.compile('\n\n+', re.UNICODE)

class Transpiler:

    def transpile(self, text):
        paragraphs = self.tokenize_paragraphs(text)
        logger.debug('paragraphs: {}'.format(paragraphs))

        self.produce_class_code({
            'name': 'Dog',
            'attributes': {
                'mood': 'HAPPY',
                'energy': 100,
                'coordinatePosition': (0, 0)
            }
        })

    def split_paragraphs(self, text):
        '''
        Returns a list of strings. Each strings is a paragraph in the
        given text.
    
        Arguments:
        text -- string assumed to contain one or more paragraphs, where a
          paragraph is defined as consecutive lines, i.e. two consecutive
          line breaks demarcate a paragraph.
        
        Usage:
        >>> two_paragraphs_together = """this is the
        ... first paragraph
        ...
        ... and this is the
        ... second
        ... """
        >>> transpiler = Transpiler()
        >>> separated_paragraphs = transpiler.split_paragraphs(two_paragraphs_together)
        >>> print(separated_paragraphs[0])
        this is the
        first paragraph
        >>> print(separated_paragraphs[1])
        and this is the
        second
        '''
        return list(map(lambda s: s.strip('\n'), paragraph_regex.split(text)))
    
    def parse_class_paragraph(self, paragraph):
        '''Returns a dictionary that contains an internal representation of
        a python class given as a natural language string *paragraph*.
        
        Arguments:
        paragraph -- str, Natural language string describing a python class.
        
        Usage:
        >>> paragraph = """
        ... A dog is a Class. He has mood = “HAPPY”, energy = 100,
        ... coordenatePosition = (0,0). He can Bark, Run, MoveLeft, MoveRight,
        ... MoveForward, Lay and Check. To Run he used MoveForward(2), his energy
        ... decreases in 1, his mood is “PLAY” and return 0. To MoveForward he
        ... needs numbersSteps, his coordinatePosition[0] increases in
        ... numbersSteps, his mood is “MOVING”, decreases energy by 1. To MoveLeft
        ... he needs numbersSteps, his coordinatePosition[1] decreases in
        ... numbersSteps, his mood is “MOVING”, decreases energy by 1. To
        ... MoveRight he needs numbersSteps, his coordinatePosition[1] increases
        ... in numbersSteps, his mood is “MOVING”, decreases energy by 1. To Bark
        ... he print “barf, barf”, his energy decreases in 1, his mood is
        ... “BARKING”. To Lay he used print “relax”, he used print “move the
        ... Booty”, his energy increases in 3. To Check he print “mood: ” +
        ... self.mood, he print “energy: “ + str(self.energy), print “Position” +
        ... str(self.coordinatePosition)
        ... """
        >>> transpiler = Transpiler()
        >>> class_metadata = transpiler.parse_class_paragraph(paragraph)
        >>> class_metadata['class_name']
        'dog'
        >>> class_metadata['property_names_and_defaults']
        [('mood', '“happy”'), ('energy', '100'), ('coordenateposition', '(0,0)')]
        '''
        # 1. Lowercase paragraph
        lowercase_paragraph = paragraph.lower()
        # 2. Tokenize words
        word_tokens = self.tokenize_words(lowercase_paragraph)
        # 3. POS-tagging
        tagged_word_tokens = self.part_of_speech_tag(word_tokens)
    
        class_name = None
        class_keyword_index = word_tokens.index('class')
        first_noun_before_class_keyword = next(filter(
            lambda pair: pair[1] == 'NN',
            tagged_word_tokens[class_keyword_index-1:0:-1]))[0]
        class_name = first_noun_before_class_keyword
        
    
        property_names_and_defaults = []
        index_of_first_word_second_sentence = (
            class_keyword_index +
            1 + # Because of the dot that finalizes the class declaration
            1 # the word after the dot
        )
        
        i = 0
        j = index_of_first_word_second_sentence
        while True:
            next_word = word_tokens[j + i]
            if next_word == '.':
                break
        
            if next_word == '=':
                # The property name is the word before the = symbol
                property_name = word_tokens[j + i - 1]
        
                # The property default value is the concatenations of all
                # the words/tokens after the = symbol and before the next
                # immediate comma or period.
                property_default_value = ''
        
                i += 1
                next_word = word_tokens[j + i]
        
                while next_word not in ('.', ','):
                    property_default_value += next_word
                    i += 1
                    next_word = word_tokens[j + i]
        
                property_names_and_defaults.append((property_name, property_default_value))
        
                i -= 1
        
            else:
                i += 1
    
        # TODO parse methods
    
        return dict(
            class_name=class_name,
            property_names_and_defaults=property_names_and_defaults
        )
    
    def produce_class_code(self, class_metadata):
        '''
        '''
        print('class {name}:'.format(**class_metadata))
        for name, value in class_metadata['attributes'].items():
            print_value=value
            if isinstance(value, str):
                print_value = '"{value}"'.format(value=value)
            print('    {name} = {value}'.format(name=name, value=print_value))
    
    def tokenize_words(self, string):
        '''Returns a list of the words contained in string which is assumed
        to be a sentence.
    
        Arguments:
        string -- string represeting a sentence
        
        Usage:
        >>> transpiler = Transpiler()
        >>> transpiler.tokenize_words('a dog is a class.')
        ['a', 'dog', 'is', 'a', 'class', '.']
        '''
        return nltk.word_tokenize(string)
    
    def part_of_speech_tag(self, tokens):
        '''Returns a list of (word, tag) tuples for each word in tokens.
    
        Tags are strings that represent the role that a word takes in a text.
        For example a tag of 'NN' means the word is a noun, a tag of 'VBZ'
        means a verb, present tense, 3rd person singular. To know what a
        particular tag means you can run the following code:
    
        nltk.help.upenn_tagset('<TAG>')
    
        Arguments:
        tokens -- list of words (str)
        
        Usage:
        >>> transpiler = Transpiler()
        >>> tokens = transpiler.tokenize_words('a dog is a class')
        >>> transpiler.part_of_speech_tag(tokens)
        [('a', 'DT'), ('dog', 'NN'), ('is', 'VBZ'), ('a', 'DT'), ('class', 'NN')]
        '''
        return nltk.pos_tag(tokens)
